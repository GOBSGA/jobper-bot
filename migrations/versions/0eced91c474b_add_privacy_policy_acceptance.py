"""add_privacy_policy_acceptance

Revision ID: 0eced91c474b
Revises: b299e2118e64
Create Date: 2026-02-11 19:51:01.574129
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers
revision: str = '0eced91c474b'
down_revision: Union[str, None] = 'b299e2118e64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not _column_exists('users', 'privacy_policy_accepted_at'):
        op.add_column('users', sa.Column('privacy_policy_accepted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    if _column_exists('users', 'privacy_policy_accepted_at'):
        op.drop_column('users', 'privacy_policy_accepted_at')
