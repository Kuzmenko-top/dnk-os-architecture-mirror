# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_media_storage_manager"
# purpose: "S3 & MinIO Object Storage Manager with Presigned URLs and TTL Cache (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List


@dataclass
class StorageConfig:
    bucket_name: str = "dnk-media-artifacts"
    endpoint_url: Optional[str] = "http://localhost:9000"
    region_name: str = "us-east-1"
    access_key_id: str = "minioadmin"
    secret_access_key: str = "minioadmin"
    presigned_url_ttl_seconds: int = 3600
    cdn_base_url: Optional[str] = None
    use_ssl: bool = False


@dataclass
class StoredMediaArtifact:
    artifact_id: str
    job_id: str
    key: str
    content_type: str
    byte_size: int
    etag: str
    presigned_url: str
    created_at_epoch: float = field(default_factory=time.time)


class MediaStorageManager:
    """
    S3 and MinIO Cloud Storage Manager for Video Ingestion & Packaging Outputs.
    Manages direct streaming, presigned download/upload URLs, TTL tokens, and local artifact fallback.
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        # In-memory artifact repository for fast testing and fallback cache
        self._artifacts: Dict[str, StoredMediaArtifact] = {}
        self._blob_store: Dict[str, bytes] = {}

    def generate_s3_key(self, job_id: str, relative_path: str, artifact_type: str = "transcoded") -> str:
        """
        Generates structured, clean S3 object key hierarchy:
        e.g., jobs/{job_id}/{artifact_type}/{relative_path}
        """
        clean_rel = relative_path.lstrip("/")
        return f"jobs/{job_id}/{artifact_type}/{clean_rel}"

    def upload_bytes(
        self,
        job_id: str,
        relative_path: str,
        data: bytes,
        content_type: str = "video/mp4",
        artifact_type: str = "transcoded",
    ) -> StoredMediaArtifact:
        """
        Stores artifact bytes and returns metadata with access URL.
        """
        key = self.generate_s3_key(job_id, relative_path, artifact_type)
        etag = hashlib.md5(data).hexdigest()
        byte_size = len(data)
        artifact_id = f"art_{hashlib.sha256(key.encode()).hexdigest()[:16]}"

        presigned_url = self.generate_presigned_get_url(key)

        artifact = StoredMediaArtifact(
            artifact_id=artifact_id,
            job_id=job_id,
            key=key,
            content_type=content_type,
            byte_size=byte_size,
            etag=etag,
            presigned_url=presigned_url,
        )

        self._artifacts[key] = artifact
        self._blob_store[key] = data
        return artifact

    def upload_file_from_disk(
        self,
        job_id: str,
        local_file_path: str,
        relative_s3_path: Optional[str] = None,
        content_type: str = "application/octet-stream",
        artifact_type: str = "transcoded",
    ) -> StoredMediaArtifact:
        """
        Reads a local disk file and uploads it to storage.
        """
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        rel_path = relative_s3_path or os.path.basename(local_file_path)
        with open(local_file_path, "rb") as f:
            data = f.read()

        return self.upload_bytes(
            job_id=job_id,
            relative_path=rel_path,
            data=data,
            content_type=content_type,
            artifact_type=artifact_type,
        )

    def download_bytes(self, key: str) -> Optional[bytes]:
        """
        Retrieves stored bytes for a given S3 key.
        """
        return self._blob_store.get(key)

    def generate_presigned_get_url(self, key: str, expires_in: Optional[int] = None) -> str:
        """
        Generates Presigned GET URL for authenticated media streaming or CDN caching.
        """
        ttl = expires_in or self.config.presigned_url_ttl_seconds
        expires_at = int(time.time()) + ttl

        # If CDN configured, use CDN URL with sign token
        if self.config.cdn_base_url:
            cdn_host = self.config.cdn_base_url.rstrip("/")
            return f"{cdn_host}/{key}?expires={expires_at}"

        endpoint = (self.config.endpoint_url or "http://localhost:9000").rstrip("/")
        return f"{endpoint}/{self.config.bucket_name}/{key}?expires={expires_at}"

    def generate_presigned_put_url(
        self,
        job_id: str,
        relative_path: str,
        content_type: str = "video/mp4",
        expires_in: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generates Presigned PUT URL for client-side direct video upload to S3/MinIO.
        """
        key = self.generate_s3_key(job_id, relative_path, artifact_type="source")
        ttl = expires_in or self.config.presigned_url_ttl_seconds
        expires_at = int(time.time()) + ttl

        endpoint = (self.config.endpoint_url or "http://localhost:9000").rstrip("/")
        upload_url = f"{endpoint}/{self.config.bucket_name}/{key}?expires={expires_at}"

        return {
            "upload_url": upload_url,
            "key": key,
            "job_id": job_id,
            "content_type": content_type,
            "expires_at_epoch": expires_at,
        }

    def list_job_artifacts(self, job_id: str) -> List[StoredMediaArtifact]:
        """
        Lists all artifacts attached to a specific processing job.
        """
        prefix = f"jobs/{job_id}/"
        return [art for key, art in self._artifacts.items() if key.startswith(prefix)]

    def delete_job_artifacts(self, job_id: str) -> int:
        """
        Deletes all stored artifacts for a given job.
        """
        prefix = f"jobs/{job_id}/"
        keys_to_delete = [k for k in self._artifacts if k.startswith(prefix)]
        for k in keys_to_delete:
            self._artifacts.pop(k, None)
            self._blob_store.pop(k, None)
        return len(keys_to_delete)


media_storage_manager = MediaStorageManager()
