"""migrate and drop old tables

Revision ID: migrate_and_drop_old_tables
Revises: 24af6a2514b2
Create Date: 2025-02-19 15:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'migrate_and_drop_old_tables'
down_revision = '24af6a2514b2'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Skapa en connection för att köra SQL
    conn = op.get_bind()

    # 1. Migrera data från users till auth_users
    conn.execute(sa.text("""
        INSERT INTO auth_users (id, email, google_id, full_name, is_active, created_at, updated_at)
        SELECT id, email, google_id, full_name, is_active, created_at, updated_at
        FROM users
        ON CONFLICT (id) DO NOTHING
    """))

    # 2. Migrera data från user_credentials till auth_user_credentials
    conn.execute(sa.text("""
        INSERT INTO auth_user_credentials (auth_user_id, token, refresh_token, token_expiry, created_at, updated_at)
        SELECT user_id, token, refresh_token, token_expiry, created_at, updated_at
        FROM user_credentials
        ON CONFLICT (auth_user_id) DO NOTHING
    """))

    # 3. Ta bort gamla tabeller
    op.drop_table('user_credentials')
    op.drop_table('users')

def downgrade() -> None:
    # Återskapa gamla tabeller
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('user_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Migrera tillbaka data
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        INSERT INTO users (id, email, google_id, full_name, is_active, created_at, updated_at)
        SELECT id, email, google_id, full_name, is_active, created_at, updated_at
        FROM auth_users
        ON CONFLICT (id) DO NOTHING
    """))

    conn.execute(sa.text("""
        INSERT INTO user_credentials (user_id, token, refresh_token, token_expiry, created_at, updated_at)
        SELECT auth_user_id, token, refresh_token, token_expiry, created_at, updated_at
        FROM auth_user_credentials
        ON CONFLICT (user_id) DO NOTHING
    """))
