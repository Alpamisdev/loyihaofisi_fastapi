"""add metadata to uploaded files

Revision ID: add_metadata_to_uploaded_files
Revises: create_uploaded_files
Create Date: 2023-11-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_metadata_to_uploaded_files'
down_revision = 'create_uploaded_files'  # This might need to be adjusted based on your actual migration history
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the uploaded_files table
    op.add_column('uploaded_files', sa.Column('title', sa.String(), nullable=True))
    op.add_column('uploaded_files', sa.Column('language', sa.String(), nullable=True))
    op.add_column('uploaded_files', sa.Column('info', sa.Text(), nullable=True))


def downgrade():
    # Remove the columns if needed to rollback
    op.drop_column('uploaded_files', 'info')
    op.drop_column('uploaded_files', 'language')
    op.drop_column('uploaded_files', 'title')
