from app.models import Company, Job


def test_job_has_company_external_id_uniqueness_constraint() -> None:
    constraints = {constraint.name for constraint in Job.__table__.constraints}

    assert "uq_jobs_company_external_id" in constraints
    assert Company.__tablename__ == "companies"

