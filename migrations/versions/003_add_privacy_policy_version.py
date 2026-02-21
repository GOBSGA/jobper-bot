"""Add privacy_policy_version to users

Revision ID: 003_add_privacy_policy_version
Revises: 0eced91c474b
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '003_add_privacy_policy_version'
down_revision = '0eced91c474b'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    if not _column_exists('users', 'privacy_policy_version'):
        op.add_column('users', sa.Column('privacy_policy_version', sa.String(20), nullable=True))


def downgrade():
    if _column_exists('users', 'privacy_policy_version'):
        op.drop_column('users', 'privacy_policy_version')
