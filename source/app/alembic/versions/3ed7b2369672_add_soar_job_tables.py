"""add_soar_job_tables

Revision ID: 3ed7b2369672
Revises: 0d65689ff496
Create Date: 2025-10-29 02:43:13.723238

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3ed7b2369672'
down_revision = '0d65689ff496'
branch_labels = None
depends_on = None


def upgrade():
    # Check if tables already exist before creating them
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create soar_jobs table only if it doesn't exist
    if 'soar_jobs' not in inspector.get_table_names():
        op.create_table('soar_jobs',
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(length=50), nullable=False),
        sa.Column('template_name', sa.String(length=200), nullable=False),
        sa.Column('integration_type', sa.String(length=50), nullable=False),
        sa.Column('target', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('executor_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('job_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], ),
        sa.ForeignKeyConstraint(['executor_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('job_id')
        )

    # Create soar_job_steps table only if it doesn't exist
    if 'soar_job_steps' not in inspector.get_table_names():
        op.create_table('soar_job_steps',
        sa.Column('step_id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('step_name', sa.String(length=200), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['soar_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('step_id')
        )

    # Create soar_job_artifacts table only if it doesn't exist
    if 'soar_job_artifacts' not in inspector.get_table_names():
        op.create_table('soar_job_artifacts',
        sa.Column('artifact_id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('artifact_name', sa.String(length=255), nullable=False),
        sa.Column('artifact_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_downloadable', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['soar_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('artifact_id')
        )

    # Create indexes for better performance (only if tables exist)
    existing_indexes = []
    for table_name in inspector.get_table_names():
        if table_name.startswith('soar_'):
            existing_indexes.extend([idx['name'] for idx in inspector.get_indexes(table_name)])

    if 'ix_soar_jobs_case_id' not in existing_indexes and 'soar_jobs' in inspector.get_table_names():
        op.create_index('ix_soar_jobs_case_id', 'soar_jobs', ['case_id'])
    if 'ix_soar_jobs_status' not in existing_indexes and 'soar_jobs' in inspector.get_table_names():
        op.create_index('ix_soar_jobs_status', 'soar_jobs', ['status'])
    if 'ix_soar_jobs_created_at' not in existing_indexes and 'soar_jobs' in inspector.get_table_names():
        op.create_index('ix_soar_jobs_created_at', 'soar_jobs', ['created_at'])
    if 'ix_soar_job_steps_job_id' not in existing_indexes and 'soar_job_steps' in inspector.get_table_names():
        op.create_index('ix_soar_job_steps_job_id', 'soar_job_steps', ['job_id'])
    if 'ix_soar_job_artifacts_job_id' not in existing_indexes and 'soar_job_artifacts' in inspector.get_table_names():
        op.create_index('ix_soar_job_artifacts_job_id', 'soar_job_artifacts', ['job_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_soar_job_artifacts_job_id', table_name='soar_job_artifacts')
    op.drop_index('ix_soar_job_steps_job_id', table_name='soar_job_steps')
    op.drop_index('ix_soar_jobs_created_at', table_name='soar_jobs')
    op.drop_index('ix_soar_jobs_status', table_name='soar_jobs')
    op.drop_index('ix_soar_jobs_case_id', table_name='soar_jobs')

    # Drop tables
    op.drop_table('soar_job_artifacts')
    op.drop_table('soar_job_steps')
    op.drop_table('soar_jobs')
