"""Add payment verification columns

Revision ID: 001
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa

revision = '001_add_verification_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add verification columns to payments table
    op.add_column('payments', sa.Column('comprobante_hash', sa.String(64), nullable=True))
    op.add_column('payments', sa.Column('verification_result', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('verification_status', sa.String(20), nullable=True))

    # Create index for duplicate detection
    op.create_index('idx_payment_hash', 'payments', ['comprobante_hash'])


def downgrade():
    op.drop_index('idx_payment_hash', table_name='payments')
    op.drop_column('payments', 'verification_status')
    op.drop_column('payments', 'verification_result')
    op.drop_column('payments', 'comprobante_hash')
