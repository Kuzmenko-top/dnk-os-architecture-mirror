# --- DNK-MRH-HEADER ---
# mrh_id: "1a2b3c4d5e6f_initial_migration.py"
# purpose: "Initial database schema migration creating canvases, snaps, design runs, artifacts, and activity events."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

"""initial migration

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2026-08-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create canvases table
    op.create_table(
        'canvases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create canvas_snapshots table
    op.create_table(
        'canvas_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('canvas_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('elements_json', sa.Text(), nullable=False),
        sa.Column('app_state_json', sa.Text(), nullable=False),
        sa.Column('files_json', sa.Text(), nullable=False),
        sa.Column('client_request_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['canvas_id'], ['canvases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create design_runs table
    op.create_table(
        'design_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('canvas_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('command', sa.String(length=255), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('artifact_id', sa.String(length=36), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['canvas_id'], ['canvases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key')
    )

    # 4. Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('canvas_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('content_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='shadow_persisted'),
        sa.Column('version', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('expires_at', sa.BigInteger(), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=True, server_default='valid'),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['canvas_id'], ['canvases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key')
    )

    # 5. Create activity_events table
    op.create_table(
        'activity_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('canvas_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('from_state', sa.String(length=50), nullable=True),
        sa.Column('to_state', sa.String(length=50), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('activity_events')
    op.drop_table('artifacts')
    op.drop_table('design_runs')
    op.drop_table('canvas_snapshots')
    op.drop_table('canvases')
