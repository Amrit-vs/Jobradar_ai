from app.models import Company, Job, Resume


def test_job_has_company_external_id_uniqueness_constraint() -> None:
    constraints = {constraint.name for constraint in Job.__table__.constraints}

    assert "uq_jobs_company_external_id" in constraints
    assert Company.__tablename__ == "companies"


def test_resume_active_index_matches_existing_migration() -> None:
    indexes = {index.name: [column.name for column in index.columns] for index in Resume.__table__.indexes}
    assert indexes["ix_resumes_user_active"] == ["user_id", "is_active"]

