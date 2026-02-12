"""add_password_hash_and_indexes

Revision ID: b299e2118e64
Revises: 002_add_trusted_payer_fields
Create Date: 2026-02-11 18:48:22.804112
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'b299e2118e64'
down_revision: Union[str, None] = '002_add_trusted_payer_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash column to users table
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Add password_hash column if it doesn't exist
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))

    # Add missing indexes for better query performance
    # These indexes were identified as critical for production performance

    # Index on User.plan (used in all billing queries)
    op.create_index(op.f('ix_users_plan'), 'users', ['plan'], unique=False)

    # Index on Contract.created_at (used in "new contracts" queries)
    op.create_index(op.f('ix_contracts_created_at'), 'contracts', ['created_at'], unique=False)

    # Index on UserContract.user_id (used in "my contracts" queries)
    op.create_index(op.f('ix_user_contracts_user_id'), 'user_contracts', ['user_id'], unique=False)

    # Index on Subscription.expires_at (used in renewal checks)
    op.create_index(op.f('ix_subscriptions_expires_at'), 'subscriptions', ['expires_at'], unique=False)

    # Index on Subscription.status (used to filter active subscriptions)
    op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'], unique=False)

    # Composite index on (user_id, created_at) for user contract history
    op.create_index('ix_user_contracts_user_created', 'user_contracts', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_user_contracts_user_created', table_name='user_contracts')
    op.drop_index(op.f('ix_subscriptions_status'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_expires_at'), table_name='subscriptions')
    op.drop_index(op.f('ix_user_contracts_user_id'), table_name='user_contracts')
    op.drop_index(op.f('ix_contracts_created_at'), table_name='contracts')
    op.drop_index(op.f('ix_users_plan'), table_name='users')

    # Drop password_hash column
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('password_hash')
