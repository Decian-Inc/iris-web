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
    # Use raw SQL with CREATE TABLE IF NOT EXISTS to handle conflicts gracefully
    op.execute("""
        CREATE TABLE IF NOT EXISTS integration_config (
            config_id SERIAL NOT NULL,
            integration_type VARCHAR(50) NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT FALSE,
            config_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            created_by VARCHAR(255),
            updated_by VARCHAR(255),
            description TEXT,
            PRIMARY KEY (config_id),
            UNIQUE (integration_type)
        )
    """)

    # Create index if it doesn't exist
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_integration_config_type
        ON integration_config (integration_type)
    """)


def downgrade():
    # Drop the table and index
    op.drop_index('ix_integration_config_type', table_name='integration_config')
    op.drop_table('integration_config')
