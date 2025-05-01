"""add token_hash column to refresh_tokens using direct SQL

Revision ID: add_token_hash_column_sql
Revises: create_refresh_tokens
Create Date: 2025-05-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

# revision identifiers, used by Alembic.
revision = 'add_token_hash_column_sql'
down_revision = 'create_refresh_tokens'
branch_labels = None
depends_on = None


def upgrade():
    # Use direct SQL to add the column
    try:
        op.execute("""
        ALTER TABLE refresh_tokens 
        ADD COLUMN token_hash VARCHAR;
        """)
        print("Added token_hash column to refresh_tokens table")
        
        # Create index
        op.execute("""
        CREATE INDEX ix_refresh_tokens_token_hash 
        ON refresh_tokens (token_hash);
        """)
        print("Created index on token_hash column")
    except OperationalError as e:
        # Column might already exist
        print(f"Note: {e}")


def downgrade():
    # SQLite doesn't support dropping columns directly
    pass
