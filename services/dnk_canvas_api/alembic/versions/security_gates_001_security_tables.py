# --- DNK-MRH-HEADER ---
# mrh_id: "alembic/versions/security_gates_001_security_tables.py"
# purpose: "Create security_gates tables for approval binding and audit trail"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# --- END DNK-MRH-HEADER ---

"""Create security_gates tables

Revision ID: security_gates_001
Revises: 2b3c4d5e6f7a
Create Date: 2026-08-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'security_gates_001'
down_revision = '2b3c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade():
    # Таблиця для approval binding
    op.create_table(
        'security_approvals',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('action_name', sa.String(255), nullable=False),
        sa.Column('args_hash', sa.String(64), nullable=False),  # SHA-256
        sa.Column('idempotency_key', sa.String(64), unique=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'timeout_rejected', name='security_approval_status'), default='pending'),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('timeout_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Індекс для швидкого пошуку по run_id + action_name
    op.create_index('idx_approvals_run_action', 'security_approvals', ['run_id', 'action_name'])
    op.create_index('idx_approvals_idempotency', 'security_approvals', ['idempotency_key'])
    
    # Таблиця для audit trail
    op.create_table(
        'security_audit_logs',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('approval_id', sa.UUID(), sa.ForeignKey('security_approvals.id')),
        sa.Column('event_type', sa.String(50), nullable=False),  # approved, rejected, timeout_rejected
        sa.Column('event_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_audit_approval', 'security_audit_logs', ['approval_id'])


def downgrade():
    op.drop_table('security_audit_logs')
    op.drop_table('security_approvals')
    
    # Drop enum type in PostgreSQL to prevent error on recreation
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS security_approval_status;')
