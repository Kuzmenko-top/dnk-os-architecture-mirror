# --- DNK-MRH-HEADER ---
# mrh_id: "alembic_versions_005_enable_workspace_rls_policies"
# purpose: "Alembic migration for Row-Level Security (RLS) enforcement on all workspace tables"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

"""Enable Row-Level Security (RLS) policies for all workspace tables

Revision ID: 005
Revises: 004
Create Date: 2026-08-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "005"
down_revision = "004"

WORKSPACE_DIRECT_TENANT_TABLES = [
    "workspaces",
    "workspace_prompts",
    "workspace_diffs",
    "workspace_approvals",
    "workspace_snapshots",
    "workspace_commits",
    "workspace_audit_trail",
    "workspace_idempotency_cache",
]

WORKSPACE_INDIRECT_TABLES = [
    "workspace_nodes",
    "workspace_edges",
]


def upgrade() -> None:
    # 1. Direct tenant_id tables RLS
    for table in WORKSPACE_DIRECT_TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            FOR ALL
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
            )
            WITH CHECK (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
            );
        """)
        op.execute(f"""
            CREATE POLICY {table}_service_role_bypass ON {table}
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
        """)

    # 2. Indirect tables RLS via workspaces join
    for table in WORKSPACE_INDIRECT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
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
        """)
        op.execute(f"""
            CREATE POLICY {table}_service_role_bypass ON {table}
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
        """)


def downgrade() -> None:
    for table in WORKSPACE_DIRECT_TENANT_TABLES + WORKSPACE_INDIRECT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_service_role_bypass ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
