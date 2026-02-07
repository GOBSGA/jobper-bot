"""Add trusted payer fields to users

Revision ID: 002
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_trusted_payer_fields'
down_revision = '001_add_verification_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Add trusted payer fields to users table
    op.add_column('users', sa.Column('trust_score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('users', sa.Column('verified_payments_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('trust_level', sa.String(20), nullable=True, server_default="'new'"))
    op.add_column('users', sa.Column('one_click_renewal_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('last_verified_payment_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'last_verified_payment_at')
    op.drop_column('users', 'one_click_renewal_enabled')
    op.drop_column('users', 'trust_level')
    op.drop_column('users', 'verified_payments_count')
    op.drop_column('users', 'trust_score')
