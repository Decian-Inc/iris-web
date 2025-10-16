"""Add FortiGate integration config

Revision ID: 0d65689ff496
Revises: 0d65689ff495
Create Date: 2025-10-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = '0d65689ff496'
down_revision = '0d65689ff495'
branch_labels = None
depends_on = None


def upgrade():
    # Insert default configuration for FortiGate integration
    op.execute(f"""
        INSERT INTO integration_config (integration_type, enabled, config_data, created_by, description)
        VALUES (
            'fortigate',
            FALSE,
            '{json.dumps({
                "api_key": "",
                "base_url": "",
                "api_version": "v2",
                "vdom": "root",
                "quarantine_duration_hours": 24,
                "verify_ssl": True
            })}',
            'system',
            'FortiGate firewall integration for automated threat containment'
        )
        ON CONFLICT (integration_type) DO NOTHING;
    """)


def downgrade():
    # Remove FortiGate integration configuration
    op.execute("DELETE FROM integration_config WHERE integration_type = 'fortigate';")