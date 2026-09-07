# --- DNK-MRH-HEADER ---
# mrh_id: "alembic_versions_006_workspace_collaboration_and_context"
# purpose: "Alembic migration for workspace_members, workspace_invitations, and user_workspace_context tables with RLS and OCC"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

"""Add workspace_members, workspace_invitations, user_workspace_context tables with RLS and OCC

Revision ID: 006
Revises: 005
Create Date: 2026-08-27

"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'


def upgrade() -> None:
    # 1. workspace_members
    op.execute("""
    CREATE TABLE IF NOT EXISTS workspace_members (
        workspace_id VARCHAR(128) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        user_id VARCHAR(128) NOT NULL,
        role VARCHAR(32) NOT NULL CHECK (role IN ('admin', 'developer', 'viewer')),
        invited_by VARCHAR(128) NOT NULL,
        invited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        status VARCHAR(32) NOT NULL CHECK (status IN ('active', 'inactive', 'suspended')),
        PRIMARY KEY (workspace_id, user_id)
    );
    """)

    # 2. workspace_invitations
    op.execute("""
    CREATE TABLE IF NOT EXISTS workspace_invitations (
        invitation_id VARCHAR(128) PRIMARY KEY,
        workspace_id VARCHAR(128) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        email VARCHAR(255) NOT NULL,
        role VARCHAR(32) NOT NULL CHECK (role IN ('admin', 'developer', 'viewer')),
        invited_by VARCHAR(128) NOT NULL,
        invited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at TIMESTAMPTZ NOT NULL,
        status VARCHAR(32) NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
        CONSTRAINT uq_workspace_email_invited UNIQUE (workspace_id, email, invited_at)
    );
    """)

    # 3. user_workspace_context
    op.execute("""
    CREATE TABLE IF NOT EXISTS user_workspace_context (
        user_id VARCHAR(128) PRIMARY KEY,
        active_workspace_id VARCHAR(128) REFERENCES workspaces(id) ON DELETE SET NULL,
        last_switched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        version INTEGER NOT NULL DEFAULT 1
    );
    """)

    # RLS Policies
    for table in ["workspace_members", "workspace_invitations"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = '{table}_tenant_isolation' AND tablename = '{table}') THEN
                CREATE POLICY {table}_tenant_isolation ON {table}
                FOR ALL
                USING (
                    EXISTS (
                        SELECT 1 FROM workspaces w
                        WHERE w.id = {table}.workspace_id
                        AND w.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
                    )
                )
                WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM workspaces w
                        WHERE w.id = {table}.workspace_id
                        AND w.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
                    )
                );
            END IF;
            END $$;
        """)

    op.execute("ALTER TABLE user_workspace_context ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_workspace_context_isolation' AND tablename = 'user_workspace_context') THEN
            CREATE POLICY user_workspace_context_isolation ON user_workspace_context
            FOR ALL
            USING (
                user_id = NULLIF(current_setting('app.current_user_id', true), '')
                OR NULLIF(current_setting('app.current_user_id', true), '') IS NULL
            );
        END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_workspace_context CASCADE;")
    op.execute("DROP TABLE IF EXISTS workspace_invitations CASCADE;")
    op.execute("DROP TABLE IF EXISTS workspace_members CASCADE;")
