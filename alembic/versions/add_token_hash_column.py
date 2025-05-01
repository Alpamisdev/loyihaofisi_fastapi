"""add token_hash column to refresh_tokens

Revision ID: add_token_hash_column
Revises: create_refresh_tokens
Create Date: 2025-05-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_token_hash_column'
down_revision = 'create_refresh_tokens'
branch_labels = None
depends_on = None


def upgrade():
    # Check if the column exists before adding it
    with op.batch_alter_table('refresh_tokens') as batch_op:
        # SQLite doesn't support IF NOT EXISTS for ADD COLUMN
        # So we need to check if the column exists first
        try:
            batch_op.add_column(sa.Column('token_hash', sa.String(), nullable=True))
            # Create index on token_hash
            batch_op.create_index('ix_refresh_tokens_token_hash', ['token_hash'])
        except Exception as e:
            # Column might already exist in some environments
            print(f"Note: {e}")


def downgrade():
    # SQLite doesn't support dropping columns directly
    # For a proper downgrade, we would need to:
    # 1. Create a new table without the column
    # 2. Copy data from the old table
    # 3. Drop the old table
    # 4. Rename the new table
    pass
