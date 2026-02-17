"""Add payment verification columns

Revision ID: 001
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = '001_add_verification_columns'
down_revision = None
branch_labels = None
depends_on = None


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


def upgrade():
    if not _column_exists('payments', 'comprobante_hash'):
        op.add_column('payments', sa.Column('comprobante_hash', sa.String(64), nullable=True))
    if not _column_exists('payments', 'verification_result'):
        op.add_column('payments', sa.Column('verification_result', sa.Text(), nullable=True))
    if not _column_exists('payments', 'verification_status'):
        op.add_column('payments', sa.Column('verification_status', sa.String(20), nullable=True))

    if not _index_exists('idx_payment_hash'):
        op.create_index('idx_payment_hash', 'payments', ['comprobante_hash'])


def downgrade():
    if _index_exists('idx_payment_hash'):
        op.drop_index('idx_payment_hash', table_name='payments')
    if _column_exists('payments', 'verification_status'):
        op.drop_column('payments', 'verification_status')
    if _column_exists('payments', 'verification_result'):
        op.drop_column('payments', 'verification_result')
    if _column_exists('payments', 'comprobante_hash'):
        op.drop_column('payments', 'comprobante_hash')
