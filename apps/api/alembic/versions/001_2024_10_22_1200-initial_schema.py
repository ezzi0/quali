"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-10-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('locale', sa.String(length=10),
                  server_default='en', nullable=False),
        sa.Column('consent_sms', sa.Boolean(),
                  server_default='false', nullable=False),
        sa.Column('consent_email', sa.Boolean(),
                  server_default='false', nullable=False),
        sa.Column('consent_whatsapp', sa.Boolean(),
                  server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contacts_email'),
                    'contacts', ['email'], unique=False)
    op.create_index(op.f('ix_contacts_phone'),
                    'contacts', ['phone'], unique=False)

    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('persona', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50),
                  server_default='new', nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_created_at'), 'leads',
                    ['created_at'], unique=False)

    # Create lead_profiles table
    op.create_table(
        'lead_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('areas', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('property_type', sa.String(length=50), nullable=True),
        sa.Column('beds', sa.Integer(), nullable=True),
        sa.Column('min_size_m2', sa.Integer(), nullable=True),
        sa.Column('budget_min', sa.Numeric(
            precision=15, scale=2), nullable=True),
        sa.Column('budget_max', sa.Numeric(
            precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3),
                  server_default='AED', nullable=False),
        sa.Column('move_in_date', sa.String(length=50), nullable=True),
        sa.Column('flexible', sa.Boolean(),
                  server_default='true', nullable=False),
        sa.Column('preapproved', sa.Boolean(), nullable=True),
        sa.Column('financing_notes', sa.String(length=500), nullable=True),
        sa.Column('preferences', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id')
    )

    # Create units table
    op.create_table(
        'units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3),
                  server_default='AED', nullable=False),
        sa.Column('area_m2', sa.Integer(), nullable=False),
        sa.Column('beds', sa.Integer(), nullable=False),
        sa.Column('baths', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('area', sa.String(length=100), nullable=True),
        sa.Column('property_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50),
                  server_default='available', nullable=False),
        sa.Column('features', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_units_location'), 'units',
                    ['location'], unique=False)
    op.create_index(op.f('ix_units_property_type'), 'units',
                    ['property_type'], unique=False)
    op.create_index(op.f('ix_units_status'), 'units', ['status'], unique=False)

    # Create qualifications table
    op.create_table(
        'qualifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('qualified', sa.Boolean(), nullable=False),
        sa.Column('reasons', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('missing_info', postgresql.ARRAY(
            sa.String()), nullable=False),
        sa.Column('suggested_next_step', sa.String(
            length=100), nullable=False),
        sa.Column('top_matches', postgresql.JSONB(
            astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qualifications_lead_id'),
                    'qualifications', ['lead_id'], unique=False)

    # Create activities table
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('payload', postgresql.JSONB(
            astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_lead_id'),
                    'activities', ['lead_id'], unique=False)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50),
                  server_default='todo', nullable=False),
        sa.Column('assignee', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_lead_id'), 'tasks',
                    ['lead_id'], unique=False)

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('session_key', sa.String(length=255), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key')
    )
    op.create_index(op.f('ix_sessions_session_key'),
                    'sessions', ['session_key'], unique=True)

    # Create auth_users table
    op.create_table(
        'auth_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50),
                  server_default='agent', nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_auth_users_email'),
                    'auth_users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_auth_users_email'), table_name='auth_users')
    op.drop_table('auth_users')
    op.drop_index(op.f('ix_sessions_session_key'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_tasks_lead_id'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_activities_lead_id'), table_name='activities')
    op.drop_table('activities')
    op.drop_index(op.f('ix_qualifications_lead_id'),
                  table_name='qualifications')
    op.drop_table('qualifications')
    op.drop_index(op.f('ix_units_status'), table_name='units')
    op.drop_index(op.f('ix_units_property_type'), table_name='units')
    op.drop_index(op.f('ix_units_location'), table_name='units')
    op.drop_table('units')
    op.drop_table('lead_profiles')
    op.drop_index(op.f('ix_leads_created_at'), table_name='leads')
    op.drop_table('leads')
    op.drop_index(op.f('ix_contacts_phone'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_email'), table_name='contacts')
    op.drop_table('contacts')
