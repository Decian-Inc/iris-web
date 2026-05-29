"""Add callback_url to client table

Revision ID: a1b2c3d4e5f6
Revises: 0d65689ff498
Create Date: 2026-05-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '0d65689ff498'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text('ALTER TABLE client ADD COLUMN IF NOT EXISTS callback_url TEXT'))


def downgrade():
    pass
