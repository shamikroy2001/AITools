"""Wave 1 Telemetry Additions to AIUsage

Revision ID: 1000_telemetry_wave1
Revises: <mock_previous_revision>
Create Date: 2024-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1000_telemetry_wave1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Operation Identifiers
    op.add_column('ai_usage', sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ai_usage', sa.Column('operation_id', postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Attribution Context
    op.add_column('ai_usage', sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ai_usage', sa.Column('module', sa.String(length=64), nullable=True))
    op.add_column('ai_usage', sa.Column('feature', sa.String(length=64), nullable=True))
    op.add_column('ai_usage', sa.Column('operation', sa.String(length=64), nullable=True))

    # 3. Cost Corrections
    # To fix the "silent zero" issue, we enforce actual_provider_cost to allow NULL and track cost_type
    op.add_column('ai_usage', sa.Column('cost_type', sa.String(length=16), server_default='UNKNOWN', nullable=False))

    # 4. Codex Financial & Exemption Boundaries
    op.add_column('ai_usage', sa.Column('billing_exemption', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('ai_usage', sa.Column('exemption_reason', sa.String(length=64), nullable=True))

    # Add query pattern indexes
    op.create_index('ix_ai_usage_created_at_module_provider', 'ai_usage', ['created_at', 'module', 'provider'])
    op.create_index('ix_ai_usage_account_id', 'ai_usage', ['account_id'])


def downgrade():
    op.drop_index('ix_ai_usage_account_id', table_name='ai_usage')
    op.drop_index('ix_ai_usage_created_at_module_provider', table_name='ai_usage')
    op.drop_column('ai_usage', 'exemption_reason')
    op.drop_column('ai_usage', 'billing_exemption')
    op.drop_column('ai_usage', 'cost_type')
    op.drop_column('ai_usage', 'operation')
    op.drop_column('ai_usage', 'feature')
    op.drop_column('ai_usage', 'module')
    op.drop_column('ai_usage', 'profile_id')
    op.drop_column('ai_usage', 'operation_id')
    op.drop_column('ai_usage', 'request_id')
