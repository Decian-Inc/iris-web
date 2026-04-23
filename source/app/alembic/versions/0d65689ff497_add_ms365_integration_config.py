"""Add MS365 integration config

Revision ID: 0d65689ff497
Revises: 0d65689ff496
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import json

revision = '0d65689ff497'
down_revision = '0d65689ff496'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(f"""
        INSERT INTO integration_config (integration_type, enabled, config_data, created_by, description)
        VALUES (
            'ms365',
            FALSE,
            '{json.dumps({
                "tenant_id": "",
                "client_id": "",
                "client_secret": "",
                "from_email": "",
                "send_email": False,
                "send_teams": False
            })}',
            'system',
            'Microsoft 365 integration for email and Teams notifications on case creation'
        )
        ON CONFLICT (integration_type) DO NOTHING;
    """)


def downgrade():
    op.execute("DELETE FROM integration_config WHERE integration_type = 'ms365';")