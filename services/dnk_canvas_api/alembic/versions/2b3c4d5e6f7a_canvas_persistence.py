# --- DNK-MRH-HEADER ---
# mrh_id: "alembic/versions/2b3c4d5e6f7a_canvas_persistence.py"
# purpose: "Create schema hub_memory and canvas persistence tables with workspace isolation and partial indexing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

"""canvas persistence tables

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-08-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7a'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create schema if not exists
    op.execute("CREATE SCHEMA IF NOT EXISTS hub_memory;")

    # 1. Create canvas_documents table under hub_memory
    op.create_table(
        'canvas_documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_type', sa.String(length=64), server_default='excalidraw', nullable=False),
        sa.Column('current_revision_id', sa.UUID(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.Column('metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    # Create indices on canvas_documents
    op.create_index('idx_canvas_docs_workspace', 'canvas_documents', ['workspace_id'], schema='hub_memory')
    op.create_index('idx_canvas_docs_status', 'canvas_documents', ['status'], schema='hub_memory')

    # 2. Create canvas_revisions table under hub_memory
    op.create_table(
        'canvas_revisions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('scene_json', sa.JSON(), nullable=False),
        sa.Column('scene_checksum', sa.String(length=64), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('parent_revision_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['hub_memory.canvas_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_revision_id'], ['hub_memory.canvas_revisions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'revision_number', name='uq_document_revision'),
        schema='hub_memory'
    )
    # Create indices on canvas_revisions
    op.create_index('idx_canvas_revisions_doc', 'canvas_revisions', ['document_id'], schema='hub_memory')
    op.create_index('idx_canvas_revisions_created', 'canvas_revisions', ['created_at'], schema='hub_memory')

    # Add foreign key constraint to canvas_documents for current_revision_id
    op.create_foreign_key(
        'fk_current_revision',
        'canvas_documents',
        'canvas_revisions',
        ['current_revision_id'],
        ['id'],
        source_schema='hub_memory',
        referent_schema='hub_memory',
        ondelete='SET NULL'
    )

    # 3. Create canvas_assets table under hub_memory (Workspace-Scoped Asset Library)
    op.create_table(
        'canvas_assets',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='pending_upload', nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=False),
        sa.Column('byte_size', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key'),
        sa.UniqueConstraint('workspace_id', 'sha256', name='uq_workspace_sha256'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_assets_workspace', 'canvas_assets', ['workspace_id'], schema='hub_memory')
    op.create_index('idx_canvas_assets_hash', 'canvas_assets', ['sha256'], schema='hub_memory')

    # 4. Create canvas_asset_links table under hub_memory (Partial Index Uniqueness)
    op.create_table(
        'canvas_asset_links',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('element_id', sa.String(length=255), nullable=True),
        sa.Column('relation_type', sa.String(length=64), server_default='references', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['hub_memory.canvas_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['hub_memory.canvas_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_asset_links_doc', 'canvas_asset_links', ['document_id'], schema='hub_memory')
    op.create_index('idx_canvas_asset_links_asset', 'canvas_asset_links', ['asset_id'], schema='hub_memory')
    
    # Dual partial indexes for canvas_asset_links
    op.execute("""
        CREATE UNIQUE INDEX uq_canvas_asset_element_link
        ON hub_memory.canvas_asset_links (document_id, element_id, asset_id)
        WHERE element_id IS NOT NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_canvas_asset_document_link
        ON hub_memory.canvas_asset_links (document_id, asset_id)
        WHERE element_id IS NULL;
    """)

    # 5. Create canvas_links table under hub_memory (Partial Index Uniqueness)
    op.create_table(
        'canvas_links',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('element_id', sa.String(length=255), nullable=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('relation_type', sa.String(length=64), server_default='references', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['hub_memory.canvas_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_links_doc', 'canvas_links', ['document_id'], schema='hub_memory')
    op.create_index('idx_canvas_links_entity', 'canvas_links', ['entity_type', 'entity_id'], schema='hub_memory')
    
    # Dual partial indexes for canvas_links
    op.execute("""
        CREATE UNIQUE INDEX uq_canvas_element_link
        ON hub_memory.canvas_links (document_id, element_id, entity_type, entity_id, relation_type)
        WHERE element_id IS NOT NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_canvas_document_link
        ON hub_memory.canvas_links (document_id, entity_type, entity_id, relation_type)
        WHERE element_id IS NULL;
    """)

    # 6. Create canvas_audit_events table under hub_memory
    op.create_table(
        'canvas_audit_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('actor_type', sa.String(length=64), nullable=False),
        sa.Column('actor_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=128), nullable=False),
        sa.Column('revision_id', sa.UUID(), nullable=True),
        sa.Column('payload', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['hub_memory.canvas_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revision_id'], ['hub_memory.canvas_revisions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_audit_doc', 'canvas_audit_events', ['document_id'], schema='hub_memory')
    op.create_index('idx_canvas_audit_actor', 'canvas_audit_events', ['actor_type', 'actor_id'], schema='hub_memory')
    op.create_index('idx_canvas_audit_type', 'canvas_audit_events', ['event_type'], schema='hub_memory')

    # 7. Create supervisor_runs table under hub_memory
    op.create_table(
        'supervisor_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('design_run_id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='queued', nullable=False),
        sa.Column('current_step', sa.Integer(), server_default='0', nullable=False),
        sa.Column('supervisor_version', sa.String(length=32), server_default='1.0.0', nullable=False),
        sa.Column('model_policy', sa.String(length=64), server_default='gemma-4', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_code', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )

    # 8. Create agent_steps table under hub_memory
    op.create_table(
        'agent_steps',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supervisor_run_id', sa.UUID(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('input_context', sa.JSON(), nullable=True),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['supervisor_run_id'], ['hub_memory.supervisor_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )

    # 9. Create tool_calls table under hub_memory
    op.create_table(
        'tool_calls',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('agent_step_id', sa.UUID(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('arguments_json', sa.JSON(), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['agent_step_id'], ['hub_memory.agent_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )

    # 10. Create approval_requests table under hub_memory
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supervisor_run_id', sa.UUID(), nullable=False),
        sa.Column('step_id', sa.UUID(), nullable=True),
        sa.Column('approval_type', sa.String(length=100), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False),
        sa.Column('proposed_action_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('requested_by', sa.String(length=255), nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supervisor_run_id'], ['hub_memory.supervisor_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )


def downgrade() -> None:
    op.drop_table('approval_requests', schema='hub_memory')
    op.drop_table('tool_calls', schema='hub_memory')
    op.drop_table('agent_steps', schema='hub_memory')
    op.drop_table('supervisor_runs', schema='hub_memory')
    op.drop_table('canvas_audit_events', schema='hub_memory')
    op.execute("""DROP INDEX IF EXISTS hub_memory.uq_canvas_element_link;""")
    op.execute("""DROP INDEX IF EXISTS hub_memory.uq_canvas_document_link;""")
    op.drop_table('canvas_links', schema='hub_memory')
    
    op.execute("""DROP INDEX IF EXISTS hub_memory.uq_canvas_asset_element_link;""")
    op.execute("""DROP INDEX IF EXISTS hub_memory.uq_canvas_asset_document_link;""")
    op.drop_table('canvas_asset_links', schema='hub_memory')
    op.drop_table('canvas_assets', schema='hub_memory')
    
    # Need to drop current_revision_id constraint or foreign key before dropping tables to prevent dependency errors
    op.drop_constraint('fk_current_revision', 'canvas_documents', schema='hub_memory', type_='foreignkey')
    
    op.drop_table('canvas_revisions', schema='hub_memory')
    op.drop_table('canvas_documents', schema='hub_memory')
    op.execute("DROP SCHEMA IF EXISTS hub_memory;")
