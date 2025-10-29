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
    # Add approval workflow columns to soar_jobs table
    op.add_column('soar_jobs', sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('soar_jobs', sa.Column('approval_status', sa.String(length=20), nullable=True))
    op.add_column('soar_jobs', sa.Column('approved_by', sa.Integer(), nullable=True))
    op.add_column('soar_jobs', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('soar_jobs', sa.Column('approval_comment', sa.Text(), nullable=True))

    # Add foreign key constraint for approved_by
    op.create_foreign_key('fk_soar_jobs_approved_by', 'soar_jobs', 'user', ['approved_by'], ['id'])

    # Add index for approval status queries
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