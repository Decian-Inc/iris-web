"""add_soar_job_scheduling

Revision ID: 5g6h7i8j9k0l
Revises: 4f5c6d7e8a9b
Create Date: 2025-10-29 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5g6h7i8j9k0l'
down_revision = '4f5c6d7e8a9b'
branch_labels = None
depends_on = None


def upgrade():
    # Check existing table structure
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns and indexes for soar_jobs table
    existing_columns = []
    existing_indexes = []

    if 'soar_jobs' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('soar_jobs')]
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('soar_jobs')]

    # Add scheduling columns to soar_jobs table only if they don't exist
    if 'scheduled_at' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))
    if 'schedule_type' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('schedule_type', sa.String(length=20), nullable=True))
    if 'schedule_params' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('schedule_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    if 'celery_task_id' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('celery_task_id', sa.String(length=255), nullable=True))
    if 'recurring_job_id' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('recurring_job_id', sa.String(length=36), nullable=True))

    # Add indexes for scheduling queries only if they don't exist
    if 'ix_soar_jobs_scheduled_at' not in existing_indexes:
        op.create_index('ix_soar_jobs_scheduled_at', 'soar_jobs', ['scheduled_at'])
    if 'ix_soar_jobs_schedule_type' not in existing_indexes:
        op.create_index('ix_soar_jobs_schedule_type', 'soar_jobs', ['schedule_type'])
    if 'ix_soar_jobs_celery_task_id' not in existing_indexes:
        op.create_index('ix_soar_jobs_celery_task_id', 'soar_jobs', ['celery_task_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_soar_jobs_celery_task_id', table_name='soar_jobs')
    op.drop_index('ix_soar_jobs_schedule_type', table_name='soar_jobs')
    op.drop_index('ix_soar_jobs_scheduled_at', table_name='soar_jobs')

    # Drop columns
    op.drop_column('soar_jobs', 'recurring_job_id')
    op.drop_column('soar_jobs', 'celery_task_id')
    op.drop_column('soar_jobs', 'schedule_params')
    op.drop_column('soar_jobs', 'schedule_type')
    op.drop_column('soar_jobs', 'scheduled_at')