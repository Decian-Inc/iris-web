"""Add integration_config table for SOAR integrations

Revision ID: 0d65689ff494
Revises: d5a720d1b99b
Create Date: 2025-10-13 22:28:49.013371

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0d65689ff494'
down_revision = 'd5a720d1b99b'
branch_labels = None
depends_on = None


def upgrade():
    # Create integration_config table
    op.create_table(
        'integration_config',
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('integration_type', sa.String(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('config_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('config_id'),
        sa.UniqueConstraint('integration_type')
    )

    # Create index on integration_type for faster lookups
    op.create_index('ix_integration_config_type', 'integration_config', ['integration_type'])


def downgrade():
    # Drop the table and index
    op.drop_index('ix_integration_config_type', table_name='integration_config')
    op.drop_table('integration_config')
