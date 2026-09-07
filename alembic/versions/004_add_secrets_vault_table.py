# --- DNK-MRH-HEADER ---
# mrh_id: "alembic_versions_004_add_secrets_vault_table"
# purpose: "Alembic migration for secrets_vault table with RLS policies (DNK-USER-WORKSPACE-MVP-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

"""Add secrets_vault table with Row-Level Security policies

Revision ID: 004
Revises: 003
Create Date: 2026-08-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004'
down_revision = '003'  # Update to previous migration ID


def upgrade() -> None:
    # Create secrets_vault table
    op.create_table(
        'secrets_vault',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('workspace_id', sa.String(36), nullable=False),
        sa.Column('secret_name', sa.String(255), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_secrets_vault_workspace_id', 'workspace_id'),
        sa.Index('ix_secrets_vault_workspace_active', 'workspace_id', 'is_active'),
        comment='Secure vault for workspace-level encrypted secrets'
    )
    
    # Enable Row-Level Security
    op.execute('ALTER TABLE secrets_vault ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy: workspace isolation
    # Users can only access rows where workspace_id matches their current tenant
    op.execute("""
        CREATE POLICY secrets_vault_workspace_isolation ON secrets_vault
        FOR ALL
        USING (
            workspace_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    
    # Create RLS policy: allow service role full access (bypass RLS for migrations/admin)
    op.execute("""
        CREATE POLICY secrets_vault_service_role_bypass ON secrets_vault
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true)
    """)
    
    # Grant permissions
    op.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON secrets_vault TO app_user')
    op.execute('GRANT USAGE, SELECT ON SEQUENCE secrets_vault_id_seq TO app_user')


def downgrade() -> None:
    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS secrets_vault_workspace_isolation ON secrets_vault')
    op.execute('DROP POLICY IF EXISTS secrets_vault_service_role_bypass ON secrets_vault')
    
    # Disable RLS
    op.execute('ALTER TABLE secrets_vault DISABLE ROW LEVEL SECURITY')
    
    # Drop table
    op.drop_table('secrets_vault')
