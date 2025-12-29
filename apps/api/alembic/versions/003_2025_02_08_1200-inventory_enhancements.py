"""inventory enhancements

Revision ID: 003_inventory
Revises: 002_marketing
Create Date: 2025-02-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_inventory'
down_revision = '002_marketing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('units', sa.Column('slug', sa.String(length=255), nullable=True))
    op.add_column('units', sa.Column('developer', sa.String(length=255), nullable=True))
    op.add_column('units', sa.Column('image_url', sa.String(length=500), nullable=True))
    op.add_column('units', sa.Column('price_display', sa.String(length=50), nullable=True))
    op.add_column('units', sa.Column('payment_plan', sa.String(length=50), nullable=True))
    op.add_column('units', sa.Column('bedrooms_label', sa.String(length=100), nullable=True))
    op.add_column('units', sa.Column('unit_sizes', sa.String(length=100), nullable=True))
    op.add_column('units', sa.Column('active', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('units', sa.Column('featured', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('units', sa.Column('handover', sa.String(length=50), nullable=True))
    op.add_column('units', sa.Column('handover_year', sa.Integer(), nullable=True))
    op.add_column('units', sa.Column('roi', sa.String(length=50), nullable=True))

    op.alter_column('units', 'area_m2', existing_type=sa.Integer(), nullable=True)
    op.alter_column('units', 'beds', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column('units', 'beds', existing_type=sa.Integer(), nullable=False)
    op.alter_column('units', 'area_m2', existing_type=sa.Integer(), nullable=False)

    op.drop_column('units', 'roi')
    op.drop_column('units', 'handover_year')
    op.drop_column('units', 'handover')
    op.drop_column('units', 'featured')
    op.drop_column('units', 'active')
    op.drop_column('units', 'unit_sizes')
    op.drop_column('units', 'bedrooms_label')
    op.drop_column('units', 'payment_plan')
    op.drop_column('units', 'price_display')
    op.drop_column('units', 'image_url')
    op.drop_column('units', 'developer')
    op.drop_column('units', 'slug')
