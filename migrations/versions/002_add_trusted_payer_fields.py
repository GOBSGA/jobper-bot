"""Add trusted payer fields to users

Revision ID: 002
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '002_add_trusted_payer_fields'
down_revision = '001_add_verification_columns'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    if not _column_exists('users', 'trust_score'):
        op.add_column('users', sa.Column('trust_score', sa.Float(), nullable=True, server_default='0.0'))
    if not _column_exists('users', 'verified_payments_count'):
        op.add_column('users', sa.Column('verified_payments_count', sa.Integer(), nullable=True, server_default='0'))
    if not _column_exists('users', 'trust_level'):
        op.add_column('users', sa.Column('trust_level', sa.String(20), nullable=True, server_default="'new'"))
    if not _column_exists('users', 'one_click_renewal_enabled'):
        op.add_column('users', sa.Column('one_click_renewal_enabled', sa.Boolean(), nullable=True, server_default='false'))
    if not _column_exists('users', 'last_verified_payment_at'):
        op.add_column('users', sa.Column('last_verified_payment_at', sa.DateTime(), nullable=True))


def downgrade():
    if _column_exists('users', 'last_verified_payment_at'):
        op.drop_column('users', 'last_verified_payment_at')
    if _column_exists('users', 'one_click_renewal_enabled'):
        op.drop_column('users', 'one_click_renewal_enabled')
    if _column_exists('users', 'trust_level'):
        op.drop_column('users', 'trust_level')
    if _column_exists('users', 'verified_payments_count'):
        op.drop_column('users', 'verified_payments_count')
    if _column_exists('users', 'trust_score'):
        op.drop_column('users', 'trust_score')
