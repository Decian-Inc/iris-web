"""add_soar_templates_table

Revision ID: 6h7i8j9k0l1m
Revises: 5g6h7i8j9k0l
Create Date: 2025-10-29 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6h7i8j9k0l1m'
down_revision = '5g6h7i8j9k0l'
branch_labels = None
depends_on = None


def upgrade():
    # Check if tables already exist before creating them
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create soar_templates table only if it doesn't exist
    if 'soar_templates' not in inspector.get_table_names():
        op.create_table('soar_templates',
        sa.Column('template_id', sa.String(length=50), nullable=False),
        sa.Column('template_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('vendor', sa.String(length=100), nullable=True),
        sa.Column('integration_type', sa.String(length=50), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('allowed_target_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('parameter_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_function', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('version', sa.String(length=20), nullable=False, server_default=sa.text("'1.0'")),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('template_id')
        )

    # Create indexes for better performance (only if table exists)
    existing_indexes = []
    if 'soar_templates' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('soar_templates')]

    if 'ix_soar_templates_integration_type' not in existing_indexes and 'soar_templates' in inspector.get_table_names():
        op.create_index('ix_soar_templates_integration_type', 'soar_templates', ['integration_type'])
    if 'ix_soar_templates_requires_approval' not in existing_indexes and 'soar_templates' in inspector.get_table_names():
        op.create_index('ix_soar_templates_requires_approval', 'soar_templates', ['requires_approval'])
    if 'ix_soar_templates_is_active' not in existing_indexes and 'soar_templates' in inspector.get_table_names():
        op.create_index('ix_soar_templates_is_active', 'soar_templates', ['is_active'])
    if 'ix_soar_templates_created_at' not in existing_indexes and 'soar_templates' in inspector.get_table_names():
        op.create_index('ix_soar_templates_created_at', 'soar_templates', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_soar_templates_created_at', table_name='soar_templates')
    op.drop_index('ix_soar_templates_is_active', table_name='soar_templates')
    op.drop_index('ix_soar_templates_requires_approval', table_name='soar_templates')
    op.drop_index('ix_soar_templates_integration_type', table_name='soar_templates')

    # Drop table
    op.drop_table('soar_templates')