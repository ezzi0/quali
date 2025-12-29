"""lead admin fields

Revision ID: 004_lead_admin
Revises: 003_inventory
Create Date: 2025-02-08 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '004_lead_admin'
down_revision = '003_inventory'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('leads', sa.Column('notes', sa.String(length=2000), nullable=True))
    op.add_column('leads', sa.Column('assigned_to', sa.String(length=255), nullable=True))
    op.add_column('leads', sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('leads', 'last_contacted_at')
    op.drop_column('leads', 'assigned_to')
    op.drop_column('leads', 'notes')
