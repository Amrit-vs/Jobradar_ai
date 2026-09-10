"""initial schema

Revision ID: 20260826_0001
Revises:
Create Date: 2026-08-26
"""
from alembic import op
import sqlalchemy as sa

revision = "20260826_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    timestamp = sa.DateTime(timezone=True)
    defaults = {"server_default": sa.text("CURRENT_TIMESTAMP")}
    op.create_table("companies", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("slug", sa.String(120), nullable=False), sa.Column("careers_url", sa.String(2048), nullable=False), sa.Column("source_type", sa.String(80), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", timestamp, nullable=False, **defaults), sa.Column("updated_at", timestamp, nullable=False, **defaults), sa.UniqueConstraint("slug", name="uq_companies_slug"))
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("created_at", timestamp, nullable=False, **defaults), sa.Column("updated_at", timestamp, nullable=False, **defaults), sa.UniqueConstraint("email", name="uq_users_email"))
    op.create_table("jobs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("external_job_id", sa.String(255), nullable=False), sa.Column("title", sa.String(500), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("location", sa.String(255), nullable=True), sa.Column("country", sa.String(100), nullable=True), sa.Column("city", sa.String(100), nullable=True), sa.Column("url", sa.String(2048), nullable=False), sa.Column("employment_type", sa.String(80), nullable=True), sa.Column("experience_level", sa.String(80), nullable=True), sa.Column("posted_at", timestamp, nullable=True), sa.Column("first_seen_at", timestamp, nullable=False), sa.Column("last_seen_at", timestamp, nullable=False), sa.Column("source", sa.String(120), nullable=False), sa.Column("status", sa.String(80), nullable=False, server_default="active"), sa.Column("created_at", timestamp, nullable=False, **defaults), sa.Column("updated_at", timestamp, nullable=False, **defaults), sa.UniqueConstraint("company_id", "external_job_id", name="uq_jobs_company_external_id"))
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_table("user_profiles", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("education", sa.Text(), nullable=True), sa.Column("degree", sa.String(255), nullable=True), sa.Column("graduation_year", sa.Integer(), nullable=True), sa.Column("years_of_experience", sa.Float(), nullable=False, server_default="0"), sa.Column("preferred_locations", sa.JSON(), nullable=False, server_default="[]"), sa.Column("preferred_roles", sa.JSON(), nullable=False, server_default="[]"), sa.Column("preferred_experience_levels", sa.JSON(), nullable=False, server_default="[]"), sa.Column("preferred_companies", sa.JSON(), nullable=False, server_default="[]"), sa.Column("skills", sa.JSON(), nullable=False, server_default="[]"), sa.Column("technologies", sa.JSON(), nullable=False, server_default="[]"), sa.Column("created_at", timestamp, nullable=False, **defaults), sa.Column("updated_at", timestamp, nullable=False, **defaults))
    op.create_table("resumes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("filename", sa.String(255), nullable=False), sa.Column("file_type", sa.String(20), nullable=False), sa.Column("extracted_text", sa.Text(), nullable=True), sa.Column("uploaded_at", timestamp, nullable=False, **defaults), sa.Column("updated_at", timestamp, nullable=False, **defaults))
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")
    op.drop_table("user_profiles")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_posted_at", table_name="jobs")
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("users")
    op.drop_table("companies")
