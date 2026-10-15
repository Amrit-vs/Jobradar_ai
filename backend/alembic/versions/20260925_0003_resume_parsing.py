"""add resume parsing fields

Revision ID: 20260925_0003
Revises: 20260908_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20260925_0003"
down_revision = "20260908_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("resumes", sa.Column("parsed_data", sa.JSON(), nullable=True))
    op.add_column("resumes", sa.Column("parsing_status", sa.String(30), nullable=False, server_default="uploaded"))
    op.add_column("resumes", sa.Column("parsing_error", sa.Text(), nullable=True))
    op.add_column("resumes", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_resumes_user_active", "resumes", ["user_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_resumes_user_active", table_name="resumes")
    op.drop_column("resumes", "is_active")
    op.drop_column("resumes", "parsing_error")
    op.drop_column("resumes", "parsing_status")
    op.drop_column("resumes", "parsed_data")
    op.drop_column("resumes", "file_size")
