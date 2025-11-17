"""marketing schema

Revision ID: 002_marketing
Revises: 001_initial
Create Date: 2024-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_marketing'
down_revision = '001_2024_10_22_1200-initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create personas table
    op.create_table(
        'personas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('characteristics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('messaging', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_personas_status', 'personas', ['status'])
    
    # Create audiences table
    op.create_table(
        'audiences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('targeting', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('estimated_size', sa.Integer(), nullable=True),
        sa.Column('size_lower', sa.Integer(), nullable=True),
        sa.Column('size_upper', sa.Integer(), nullable=True),
        sa.Column('platform_audience_id', sa.String(length=200), nullable=True),
        sa.Column('platform_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audiences_persona', 'audiences', ['persona_id'])
    op.create_index('idx_audiences_platform', 'audiences', ['platform', 'status'])
    
    # Create creatives table
    op.create_table(
        'creatives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('headline', sa.String(length=255), nullable=True),
        sa.Column('primary_text', sa.Text(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('call_to_action', sa.String(length=50), nullable=True),
        sa.Column('media', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('risk_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('generation_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('variants', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_creatives_persona', 'creatives', ['persona_id'])
    op.create_index('idx_creatives_status', 'creatives', ['status'])
    
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('objective', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('budget_total', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('budget_daily', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='AED'),
        sa.Column('spend_total', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('spend_today', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('platform_campaign_id', sa.String(length=200), nullable=True),
        sa.Column('platform_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('strategy', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_campaigns_status', 'campaigns', ['status'])
    op.create_index('idx_campaigns_platform', 'campaigns', ['platform', 'status'])
    
    # Create ad_sets table
    op.create_table(
        'ad_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('audience_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('budget_daily', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('bid_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('bid_strategy', sa.String(length=50), nullable=True),
        sa.Column('spend_total', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('spend_today', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('geo', sa.String(length=200), nullable=True),
        sa.Column('schedule', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('platform_adset_id', sa.String(length=200), nullable=True),
        sa.Column('platform_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('optimization_goal', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['audience_id'], ['audiences.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_adsets_campaign', 'ad_sets', ['campaign_id'])
    
    # Create ads table
    op.create_table(
        'ads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ad_set_id', sa.Integer(), nullable=False),
        sa.Column('creative_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('platform_ad_id', sa.String(length=200), nullable=True),
        sa.Column('platform_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('tracking_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ad_set_id'], ['ad_sets.id'], ),
        sa.ForeignKeyConstraint(['creative_id'], ['creatives.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ads_adset', 'ads', ['ad_set_id'])
    
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('hypothesis', sa.String(length=1000), nullable=False),
        sa.Column('design', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('confidence_level', sa.Float(), nullable=False, server_default='0.95'),
        sa.Column('minimum_sample_size', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('mde', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stop_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stop_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_experiments_persona', 'experiments', ['persona_id'])
    op.create_index('idx_experiments_status', 'experiments', ['status'])
    
    # Create marketing_metrics table
    op.create_table(
        'marketing_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('ad_set_id', sa.Integer(), nullable=True),
        sa.Column('ad_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reach', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('likes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shares', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('saves', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('leads', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('qualified_leads', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('appointments', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('viewings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contracts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('closed_won', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('spend', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('revenue', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='AED'),
        sa.Column('ctr', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cpc', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('cpl', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('cpa', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('roas', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('conversion_rate', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('platform_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['ad_set_id'], ['ad_sets.id'], ),
        sa.ForeignKeyConstraint(['ad_id'], ['ads.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'campaign_id', 'ad_set_id', 'ad_id', name='uix_metrics_date_campaign_adset_ad')
    )
    op.create_index('idx_metrics_date', 'marketing_metrics', ['date'], postgresql_ops={'date': 'DESC'})
    op.create_index('idx_metrics_campaign', 'marketing_metrics', ['campaign_id'])
    
    # Add marketing columns to leads table
    op.add_column('leads', sa.Column('marketing_persona_id', sa.Integer(), nullable=True))
    op.add_column('leads', sa.Column('attribution_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_foreign_key('fk_leads_marketing_persona', 'leads', 'personas', ['marketing_persona_id'], ['id'])
    
    # Add marketing columns to qualifications table
    op.add_column('qualifications', sa.Column('predicted_ltv', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('qualifications', sa.Column('acquisition_cost', sa.Numeric(precision=15, scale=2), nullable=True))


def downgrade() -> None:
    # Remove marketing columns from qualifications
    op.drop_column('qualifications', 'acquisition_cost')
    op.drop_column('qualifications', 'predicted_ltv')
    
    # Remove marketing columns from leads
    op.drop_constraint('fk_leads_marketing_persona', 'leads', type_='foreignkey')
    op.drop_column('leads', 'attribution_data')
    op.drop_column('leads', 'marketing_persona_id')
    
    # Drop marketing tables in reverse order
    op.drop_index('idx_metrics_campaign', table_name='marketing_metrics')
    op.drop_index('idx_metrics_date', table_name='marketing_metrics')
    op.drop_table('marketing_metrics')
    
    op.drop_index('idx_experiments_status', table_name='experiments')
    op.drop_index('idx_experiments_persona', table_name='experiments')
    op.drop_table('experiments')
    
    op.drop_index('idx_ads_adset', table_name='ads')
    op.drop_table('ads')
    
    op.drop_index('idx_adsets_campaign', table_name='ad_sets')
    op.drop_table('ad_sets')
    
    op.drop_index('idx_campaigns_platform', table_name='campaigns')
    op.drop_index('idx_campaigns_status', table_name='campaigns')
    op.drop_table('campaigns')
    
    op.drop_index('idx_creatives_status', table_name='creatives')
    op.drop_index('idx_creatives_persona', table_name='creatives')
    op.drop_table('creatives')
    
    op.drop_index('idx_audiences_platform', table_name='audiences')
    op.drop_index('idx_audiences_persona', table_name='audiences')
    op.drop_table('audiences')
    
    op.drop_index('idx_personas_status', table_name='personas')
    op.drop_table('personas')

