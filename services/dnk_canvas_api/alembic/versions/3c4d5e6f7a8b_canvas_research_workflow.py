# --- DNK-MRH-HEADER ---
# mrh_id: "alembic/versions/3c4d5e6f7a8b_canvas_research_workflow.py"
# purpose: "Create canvas competitors, evidences, insights, and flower drafts tables in hub_memory schema"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

"""create canvas research workflow tables

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-08-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3c4d5e6f7a8b'
down_revision = 'security_gates_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create canvas_competitors table under hub_memory
    op.create_table(
        'canvas_competitors',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website_url', sa.String(length=512), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.Column('metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_competitors_workspace', 'canvas_competitors', ['workspace_id'], schema='hub_memory')

    # 2. Create canvas_evidences table under hub_memory
    op.create_table(
        'canvas_evidences',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('competitor_id', sa.UUID(), nullable=True),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('source_url', sa.String(length=512), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('evidence_status', sa.String(length=32), server_default='captured', nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('storage_mode', sa.String(length=32), server_default='fixture', nullable=False),
        sa.Column('metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['competitor_id'], ['hub_memory.canvas_competitors.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['asset_id'], ['hub_memory.canvas_assets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'sha256', name='uq_workspace_evidence_sha256'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_evidences_workspace', 'canvas_evidences', ['workspace_id'], schema='hub_memory')
    op.create_index('idx_canvas_evidences_sha256', 'canvas_evidences', ['sha256'], schema='hub_memory')

    # 3. Create canvas_insights table under hub_memory
    op.create_table(
        'canvas_insights',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('element_id', sa.String(length=255), nullable=False),
        sa.Column('evidence_id', sa.UUID(), nullable=True),
        sa.Column('competitor_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='proposed', nullable=False),
        sa.Column('source_references', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['hub_memory.canvas_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['evidence_id'], ['hub_memory.canvas_evidences.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['competitor_id'], ['hub_memory.canvas_competitors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    op.create_index('idx_canvas_insights_workspace', 'canvas_insights', ['workspace_id'], schema='hub_memory')
    op.create_index('idx_canvas_insights_element', 'canvas_insights', ['document_id', 'element_id'], schema='hub_memory')

    # 4. Create flower_drafts table under hub_memory
    op.create_table(
        'flower_drafts',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('element_id', sa.String(length=255), nullable=False),
        sa.Column('insight_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='draft', nullable=False),
        sa.Column('flower_type', sa.String(length=64), server_default='task_flower', nullable=False),
        sa.Column('content', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('source_references', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['hub_memory.canvas_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['insight_id'], ['hub_memory.canvas_insights.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='hub_memory'
    )
    op.create_index('idx_flower_drafts_workspace', 'flower_drafts', ['workspace_id'], schema='hub_memory')
    op.create_index('idx_flower_drafts_element', 'flower_drafts', ['document_id', 'element_id'], schema='hub_memory')

def downgrade() -> None:
    op.drop_table('flower_drafts', schema='hub_memory')
    op.drop_table('canvas_insights', schema='hub_memory')
    op.drop_table('canvas_evidences', schema='hub_memory')
    op.drop_table('canvas_competitors', schema='hub_memory')
