"""add_password_hash_and_indexes

Revision ID: b299e2118e64
Revises: 002_add_trusted_payer_fields
Create Date: 2026-02-11 18:48:22.804112
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers
revision: str = 'b299e2118e64'
down_revision: Union[str, None] = '002_add_trusted_payer_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def _index_exists(index_name):
    bind = op.get_bind()
    result = bind.execute(
        text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
        {"name": index_name}
    )
    return result.fetchone() is not None


def _table_exists(table_name):
    bind = op.get_bind()
    result = bind.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_name = :name"),
        {"name": table_name}
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not _column_exists('users', 'password_hash'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))

    if not _index_exists('ix_users_plan'):
        op.create_index(op.f('ix_users_plan'), 'users', ['plan'], unique=False)

    if _table_exists('contracts') and not _index_exists('ix_contracts_created_at'):
        op.create_index(op.f('ix_contracts_created_at'), 'contracts', ['created_at'], unique=False)

    # Only create user_contracts indexes if table exists
    if _table_exists('user_contracts'):
        if not _index_exists('ix_user_contracts_user_id'):
            op.create_index(op.f('ix_user_contracts_user_id'), 'user_contracts', ['user_id'], unique=False)
        if not _index_exists('ix_user_contracts_user_created'):
            op.create_index('ix_user_contracts_user_created', 'user_contracts', ['user_id', 'created_at'], unique=False)

    # Only create subscriptions indexes if table and columns exist
    if _table_exists('subscriptions'):
        if _column_exists('subscriptions', 'expires_at') and not _index_exists('ix_subscriptions_expires_at'):
            op.create_index(op.f('ix_subscriptions_expires_at'), 'subscriptions', ['expires_at'], unique=False)
        if _column_exists('subscriptions', 'status') and not _index_exists('ix_subscriptions_status'):
            op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'], unique=False)


def downgrade() -> None:
    if _index_exists('ix_user_contracts_user_created'):
        op.drop_index('ix_user_contracts_user_created', table_name='user_contracts')
    if _index_exists('ix_subscriptions_status'):
        op.drop_index(op.f('ix_subscriptions_status'), table_name='subscriptions')
    if _index_exists('ix_subscriptions_expires_at'):
        op.drop_index(op.f('ix_subscriptions_expires_at'), table_name='subscriptions')
    if _index_exists('ix_user_contracts_user_id'):
        op.drop_index(op.f('ix_user_contracts_user_id'), table_name='user_contracts')
    if _index_exists('ix_contracts_created_at'):
        op.drop_index(op.f('ix_contracts_created_at'), table_name='contracts')
    if _index_exists('ix_users_plan'):
        op.drop_index(op.f('ix_users_plan'), table_name='users')

    if _column_exists('users', 'password_hash'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('password_hash')
