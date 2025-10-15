"""Add HaveIBeenPwned integration config

Revision ID: 0d65689ff495
Revises: 0d65689ff494
Create Date: 2025-10-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = '0d65689ff495'
down_revision = '0d65689ff494'
branch_labels = None
depends_on = None


def upgrade():
    # Insert default configuration for HaveIBeenPwned integration
    op.execute(f"""
        INSERT INTO integration_config (integration_type, enabled, config_data, created_by, description)
        VALUES (
            'haveibeenpwned',
            FALSE,
            '{json.dumps({
                "api_key": "",
                "base_url": "https://haveibeenpwned.com/api/v3",
                "verify_ssl": True,
                "rate_limit_delay": 1.6
            })}',
            'system',
            'HaveIBeenPwned credential exposure intelligence integration'
        )
        ON CONFLICT (integration_type) DO NOTHING;
    """)


def downgrade():
    # Remove HaveIBeenPwned integration configuration
    op.execute("DELETE FROM integration_config WHERE integration_type = 'haveibeenpwned';")