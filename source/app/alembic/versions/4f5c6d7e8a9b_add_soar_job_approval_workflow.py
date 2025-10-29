"""add_soar_job_approval_workflow

Revision ID: 4f5c6d7e8a9b
Revises: 3ed7b2369672
Create Date: 2025-10-29 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4f5c6d7e8a9b'
down_revision = '3ed7b2369672'
branch_labels = None
depends_on = None


def upgrade():
    # Check existing table structure
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns for soar_jobs table
    existing_columns = []
    existing_constraints = []
    existing_indexes = []

    if 'soar_jobs' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('soar_jobs')]
        existing_constraints = [fk['name'] for fk in inspector.get_foreign_keys('soar_jobs')]
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('soar_jobs')]

    # Add approval workflow columns to soar_jobs table only if they don't exist
    if 'requires_approval' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    if 'approval_status' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('approval_status', sa.String(length=20), nullable=True))
    if 'approved_by' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('approved_by', sa.Integer(), nullable=True))
    if 'approved_at' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    if 'approval_comment' not in existing_columns:
        op.add_column('soar_jobs', sa.Column('approval_comment', sa.Text(), nullable=True))

    # Add foreign key constraint for approved_by only if it doesn't exist
    if 'fk_soar_jobs_approved_by' not in existing_constraints:
        op.create_foreign_key('fk_soar_jobs_approved_by', 'soar_jobs', 'user', ['approved_by'], ['id'])

    # Add index for approval status queries only if it doesn't exist
    if 'ix_soar_jobs_approval_status' not in existing_indexes:
        op.create_index('ix_soar_jobs_approval_status', 'soar_jobs', ['approval_status'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_soar_jobs_approval_status', table_name='soar_jobs')

    # Drop foreign key constraint
    op.drop_constraint('fk_soar_jobs_approved_by', 'soar_jobs', type_='foreignkey')

    # Drop columns
    op.drop_column('soar_jobs', 'approval_comment')
    op.drop_column('soar_jobs', 'approved_at')
    op.drop_column('soar_jobs', 'approved_by')
    op.drop_column('soar_jobs', 'approval_status')
    op.drop_column('soar_jobs', 'requires_approval')