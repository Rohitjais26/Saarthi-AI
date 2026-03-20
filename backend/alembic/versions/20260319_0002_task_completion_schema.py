"""expand schema for full task coverage

Revision ID: 20260319_0002
Revises: 20260211_0001
Create Date: 2026-03-19 00:00:02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260319_0002'
down_revision: Union[str, Sequence[str], None] = '20260211_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('geography') as batch:
        batch.add_column(sa.Column('youth_population', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('female_participation_rate', sa.Float(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('unemployment_rate', sa.Float(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('median_household_income', sa.Float(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('internet_penetration_rate', sa.Float(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('skill_gap_index', sa.Float(), nullable=False, server_default='0'))

    with op.batch_alter_table('youth_profile') as batch:
        batch.add_column(sa.Column('education_level', sa.String(length=50), nullable=True))
        batch.add_column(sa.Column('employment_status', sa.String(length=50), nullable=True))
        batch.add_column(sa.Column('household_income_band', sa.String(length=30), nullable=True))

    with op.batch_alter_table('segmentation_score') as batch:
        batch.add_column(sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'))
        batch.add_column(sa.Column('recommended_channels_json', sa.JSON(), nullable=False, server_default='{}'))

    with op.batch_alter_table('campaign') as batch:
        batch.add_column(sa.Column('deployment_mode', sa.String(length=30), nullable=False, server_default='manual'))
        batch.add_column(sa.Column('deployed_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('onboarding_case') as batch:
        batch.add_column(sa.Column('documents_json', sa.JSON(), nullable=False, server_default='{}'))
        batch.add_column(sa.Column('reminder_count', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('last_reminder_ts', sa.DateTime(), nullable=True))

    op.create_table(
        'regional_skill_snapshot',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('state_code', sa.String(length=10), nullable=False),
        sa.Column('district_code', sa.String(length=20), nullable=False),
        sa.Column('source', sa.String(length=120), nullable=False, server_default='manual_upload'),
        sa.Column('demographics_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('economics_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('skills_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('ts', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_regional_skill_snapshot_state_code', 'regional_skill_snapshot', ['state_code'])
    op.create_index('ix_regional_skill_snapshot_district_code', 'regional_skill_snapshot', ['district_code'])
    op.create_index('ix_regional_skill_snapshot_ts', 'regional_skill_snapshot', ['ts'])

    op.create_table(
        'message_dispatch',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('campaign_id', sa.String(length=64), sa.ForeignKey('campaign.id'), nullable=False),
        sa.Column('lead_id', sa.String(length=64), sa.ForeignKey('youth_profile.id'), nullable=False),
        sa.Column('channel', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='queued'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('provider_message_id', sa.String(length=128), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_message_dispatch_campaign_id', 'message_dispatch', ['campaign_id'])
    op.create_index('ix_message_dispatch_lead_id', 'message_dispatch', ['lead_id'])
    op.create_index('ix_message_dispatch_channel', 'message_dispatch', ['channel'])
    op.create_index('ix_message_dispatch_status', 'message_dispatch', ['status'])


def downgrade() -> None:
    op.drop_index('ix_message_dispatch_status', table_name='message_dispatch')
    op.drop_index('ix_message_dispatch_channel', table_name='message_dispatch')
    op.drop_index('ix_message_dispatch_lead_id', table_name='message_dispatch')
    op.drop_index('ix_message_dispatch_campaign_id', table_name='message_dispatch')
    op.drop_table('message_dispatch')

    op.drop_index('ix_regional_skill_snapshot_ts', table_name='regional_skill_snapshot')
    op.drop_index('ix_regional_skill_snapshot_district_code', table_name='regional_skill_snapshot')
    op.drop_index('ix_regional_skill_snapshot_state_code', table_name='regional_skill_snapshot')
    op.drop_table('regional_skill_snapshot')

    with op.batch_alter_table('onboarding_case') as batch:
        batch.drop_column('last_reminder_ts')
        batch.drop_column('reminder_count')
        batch.drop_column('documents_json')

    with op.batch_alter_table('campaign') as batch:
        batch.drop_column('deployed_at')
        batch.drop_column('deployment_mode')

    with op.batch_alter_table('segmentation_score') as batch:
        batch.drop_column('recommended_channels_json')
        batch.drop_column('confidence_score')

    with op.batch_alter_table('youth_profile') as batch:
        batch.drop_column('household_income_band')
        batch.drop_column('employment_status')
        batch.drop_column('education_level')

    with op.batch_alter_table('geography') as batch:
        batch.drop_column('skill_gap_index')
        batch.drop_column('internet_penetration_rate')
        batch.drop_column('median_household_income')
        batch.drop_column('unemployment_rate')
        batch.drop_column('female_participation_rate')
        batch.drop_column('youth_population')
