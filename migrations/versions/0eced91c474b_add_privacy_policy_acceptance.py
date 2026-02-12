"""add_privacy_policy_acceptance

Revision ID: 0eced91c474b
Revises: b299e2118e64
Create Date: 2026-02-11 19:51:01.574129
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '0eced91c474b'
down_revision: Union[str, None] = 'b299e2118e64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add privacy_policy_accepted_at column to users table
    op.add_column('users', sa.Column('privacy_policy_accepted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove privacy_policy_accepted_at column from users table
    op.drop_column('users', 'privacy_policy_accepted_at')
