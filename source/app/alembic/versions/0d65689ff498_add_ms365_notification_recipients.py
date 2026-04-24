"""Add MS365 notification recipients table

Revision ID: 0d65689ff498
Revises: 0d65689ff497
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = '0d65689ff498'
down_revision = '0d65689ff497'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table already exists before creating
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'ms365_notification_recipients' not in inspector.get_table_names():
        op.create_table(
            'ms365_notification_recipients',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('channel_type', sa.String(10), nullable=False),
            sa.Column('address', sa.Text(), nullable=False),
            sa.Column('display_name', sa.String(255), nullable=True),
            sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('created_by', sa.String(255), nullable=True)
        )
        op.create_index('ix_ms365_recipients_channel', 'ms365_notification_recipients', ['channel_type'])


def downgrade():
    # Check if table exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'ms365_notification_recipients' in inspector.get_table_names():
        op.drop_index('ix_ms365_recipients_channel', table_name='ms365_notification_recipients')
        op.drop_table('ms365_notification_recipients')