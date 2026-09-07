# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_secrets_vault_service"
# purpose: "Business logic layer for Secrets Vault with Fernet encryption/decryption (DNK-USER-WORKSPACE-MVP-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import Optional, List, Dict, Any, Tuple
try:
    from apps.api.repositories.secrets_vault_repository import SecretsVaultRepository
except ImportError:
    from repositories.secrets_vault_repository import SecretsVaultRepository

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import os
import logging
import base64
import hashlib

logger = logging.getLogger(__name__)


class SecretsVaultServiceError(Exception):
    """Base exception for Secrets Vault service errors."""
    pass


class SecretNotFoundError(SecretsVaultServiceError):
    """Raised when a requested secret does not exist or is inactive."""
    pass


class SecretDecryptionError(SecretsVaultServiceError):
    """Raised when decryption fails due to invalid token or key mismatch."""
    pass


class SecretEncryptionError(SecretsVaultServiceError):
    """Raised when encryption fails."""
    pass


class SecretsVaultService:
    """
    High-level service for secure secrets management.
    
    Handles:
    - Fernet symmetric encryption/decryption
    - Key derivation from environment variables
    - Workspace-scoped CRUD operations via repository
    - Audit logging for all operations
    
    Security properties:
    - Plaintext secrets never stored in database
    - Encryption key loaded from environment (SECRET_ENCRYPTION_KEY)
    - All operations scoped to workspace_id for tenant isolation
    """
    
    def __init__(self, repository: SecretsVaultRepository, encryption_key: Optional[str] = None):
        """
        Initialize service with repository and encryption key.
        
        Args:
            repository: SecretsVaultRepository instance
            encryption_key: Fernet-compatible key (32 url-safe base64-encoded bytes).
                           If None, loads from SECRET_ENCRYPTION_KEY environment variable.
        
        Raises:
            ValueError: If encryption key is invalid or missing
        """
        self.repository = repository
        
        if encryption_key is None:
            encryption_key = os.getenv("SECRET_ENCRYPTION_KEY")
        
        if not encryption_key:
            raise ValueError(
                "SECRET_ENCRYPTION_KEY environment variable is not set. "
                "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        try:
            self.cipher = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid Fernet encryption key: {e}")
        
        logger.info("SecretsVaultService initialized with Fernet encryption")
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            32-byte url-safe base64-encoded key
        
        Usage:
            python -c "from services.secrets_vault_service import SecretsVaultService; print(SecretsVaultService.generate_key())"
        """
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """
        Derive a Fernet-compatible key from a password using PBKDF2-HMAC-SHA256.
        
        Args:
            password: User-provided password
            salt: Optional salt (32 bytes). If None, generates random salt.
        
        Returns:
            Tuple of (derived_key, salt)
        
        Note:
            Store salt alongside encrypted data for future decryption.
        """
        if salt is None:
            salt = os.urandom(32)
        
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            dklen=32
        )
        
        # Fernet requires url-safe base64 encoding
        key = base64.urlsafe_b64encode(derived).decode()
        return key, salt
    
    async def store_secret(
        self,
        workspace_id: str,
        secret_name: str,
        plaintext_value: str
    ) -> str:
        """
        Encrypt and store a new secret.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_name: Human-readable identifier
            plaintext_value: Secret value in plaintext (will be encrypted)
        
        Returns:
            Secret ID (UUID)
        
        Raises:
            SecretEncryptionError: If encryption fails
            IntegrityError: If duplicate secret_name exists for workspace
            SQLAlchemyError: On database errors
        """
        try:
            encrypted = self.cipher.encrypt(plaintext_value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed for secret '{secret_name}': {e}")
            raise SecretEncryptionError(f"Failed to encrypt secret: {e}")
        
        try:
            secret = await self.repository.create_secret(
                workspace_id=workspace_id,
                secret_name=secret_name,
                encrypted_value=encrypted
            )
            logger.info(f"Stored secret '{secret_name}' for workspace {workspace_id}")
            return secret.id
        except IntegrityError as e:
            logger.error(f"Duplicate secret name '{secret_name}' in workspace {workspace_id}: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error storing secret '{secret_name}': {e}")
            raise
    
    async def retrieve_secret(
        self,
        workspace_id: str,
        secret_id: Optional[str] = None,
        secret_name: Optional[str] = None
    ) -> str:
        """
        Retrieve and decrypt a secret by ID or name.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_id: Secret UUID (optional if secret_name provided)
            secret_name: Human-readable identifier (optional if secret_id provided)
        
        Returns:
            Decrypted plaintext value
        
        Raises:
            SecretNotFoundError: If secret not found or inactive
            SecretDecryptionError: If decryption fails
            ValueError: If neither secret_id nor secret_name provided
        """
        if not secret_id and not secret_name:
            raise ValueError("Either secret_id or secret_name must be provided")
        
        try:
            if secret_id:
                secret = await self.repository.get_secret(workspace_id, secret_id)
            elif secret_name:
                secret = await self.repository.get_secret_by_name(workspace_id, secret_name)
            else:
                raise ValueError("Either secret_id or secret_name must be provided")
            
            if not secret:
                identifier = secret_id or secret_name
                logger.warning(f"Secret '{identifier}' not found in workspace {workspace_id}")
                raise SecretNotFoundError(f"Secret '{identifier}' not found or inactive")
            
            try:
                decrypted = self.cipher.decrypt(secret.encrypted_value.encode('utf-8')).decode('utf-8')
                logger.info(f"Retrieved secret '{secret.secret_name}' for workspace {workspace_id}")
                return decrypted
            except InvalidToken as e:
                logger.error(f"Decryption failed for secret {secret.id}: invalid token or key mismatch")
                raise SecretDecryptionError(f"Failed to decrypt secret: {e}")
        
        except SecretNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving secret: {e}")
            raise SecretNotFoundError(f"Database error: {e}")
    
    async def update_secret(
        self,
        workspace_id: str,
        secret_id: str,
        plaintext_value: str
    ) -> bool:
        """
        Update an existing secret with a new encrypted value.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_id: Secret UUID
            plaintext_value: New plaintext value (will be encrypted)
        
        Returns:
            True if updated successfully
        
        Raises:
            SecretNotFoundError: If secret not found
            SecretEncryptionError: If encryption fails
        """
        secret = await self.repository.get_secret(workspace_id, secret_id)
        if not secret:
            raise SecretNotFoundError(f"Secret '{secret_id}' not found or inactive")
        
        try:
            encrypted = self.cipher.encrypt(plaintext_value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed for secret update {secret_id}: {e}")
            raise SecretEncryptionError(f"Failed to encrypt secret: {e}")
        
        updated = await self.repository.update_secret(workspace_id, secret_id, encrypted)
        if updated:
            logger.info(f"Updated secret {secret_id} for workspace {workspace_id}")
        return updated
    
    async def revoke_secret(
        self,
        workspace_id: str,
        secret_id: str
    ) -> bool:
        """
        Soft-delete a secret (set is_active = False).
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_id: Secret UUID
        
        Returns:
            True if revoked successfully, False if not found
        """
        revoked = await self.repository.deactivate_secret(workspace_id, secret_id)
        if revoked:
            logger.info(f"Revoked secret {secret_id} for workspace {workspace_id}")
        return revoked
    
    async def list_secret_metadata(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List metadata for active secrets (without exposing encrypted values).
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of dicts with id, secret_name, created_at, updated_at
        """
        secrets = await self.repository.list_secrets(workspace_id, limit, offset)
        return [
            {
                "id": s.id,
                "secret_name": s.secret_name,
                "created_at": s.created_at.isoformat() if hasattr(s.created_at, "isoformat") else str(s.created_at),
                "updated_at": s.updated_at.isoformat() if hasattr(s.updated_at, "isoformat") else str(s.updated_at)
            }
            for s in secrets
        ]
    
    async def count_secrets(self, workspace_id: str) -> int:
        """
        Count active secrets for a workspace.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
        
        Returns:
            Number of active secrets
        """
        return await self.repository.count_secrets(workspace_id)
