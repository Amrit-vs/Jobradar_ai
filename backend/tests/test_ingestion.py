from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import CollectionRun, Company, Job
from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.registry import CompanyAdapterRegistry
from app.services.ingestion import JobIngestionService


def database() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, autoflush=False)


def test_collecting_twice_preserves_job_count_and_first_seen() -> None:
    db = database()
    service = JobIngestionService(db)
    first = service.collect_all()
    jobs = db.scalars(select(Job)).all()
    initial_seen = {job.external_job_id: job.first_seen_at for job in jobs}
    second = service.collect_all()

    assert first.jobs_added == 25
    assert len(db.scalars(select(Job)).all()) == 25
    assert second.jobs_added == 0
    assert second.jobs_updated == 0
    assert second.duplicates == 25
    assert all(job.first_seen_at == initial_seen[job.external_job_id] for job in db.scalars(select(Job)))
    assert len(db.scalars(select(CollectionRun)).all()) == 10


class FailingAdapter(JobSourceAdapter):
    slug = "broken"
    careers_url = "https://example.invalid/broken"
    def get_company(self) -> str: return "Broken"
    def fetch_jobs(self) -> list[NormalizedJob]: raise RuntimeError("offline test failure")


def test_adapter_failure_does_not_stop_other_adapters() -> None:
    db = database()
    registry = CompanyAdapterRegistry([FailingAdapter(), CompanyAdapterRegistry().enabled_adapters()[0]])
    result = JobIngestionService(db, registry).collect_all()

    assert result.errors == 1
    assert result.jobs_added == 5


def test_existing_job_is_updated_without_replacement() -> None:
    db = database()
    adapter = CompanyAdapterRegistry().enabled_adapters()[0]
    service = JobIngestionService(db, CompanyAdapterRegistry([adapter]))
    service.collect_all()
    original = db.scalar(select(Job))
    original_id, first_seen = original.id, original.first_seen_at
    altered = adapter.fetch_jobs()
    altered[0] = altered[0].model_copy(update={"title": "Updated Software Engineer"})

    class ChangedAdapter(JobSourceAdapter):
        slug, careers_url = adapter.slug, adapter.careers_url
        def get_company(self) -> str: return adapter.get_company()
        def fetch_jobs(self) -> list[NormalizedJob]: return altered

    result = JobIngestionService(db, CompanyAdapterRegistry([ChangedAdapter()])).collect_all()
    updated = db.scalar(select(Job).where(Job.external_job_id == altered[0].external_job_id))
    assert result.jobs_updated == 1
    assert result.jobs_added == 0
    assert result.duplicates == 4
    assert updated.id == original_id
    assert updated.first_seen_at == first_seen
    assert updated.title == "Updated Software Engineer"


def adapter_with_jobs(jobs: list[NormalizedJob]) -> JobSourceAdapter:
    class BatchAdapter(JobSourceAdapter):
        slug = "batch"
        careers_url = "https://example.invalid/batch"

        def get_company(self) -> str:
            return "Batch"

        def fetch_jobs(self) -> list[NormalizedJob]:
            return jobs

    return BatchAdapter()


def test_duplicate_ids_in_one_batch_are_deduplicated() -> None:
    db = database()
    job = CompanyAdapterRegistry().enabled_adapters()[0].fetch_jobs()[0]
    result = JobIngestionService(db, CompanyAdapterRegistry([adapter_with_jobs([job, job])])).collect_all()
    assert result.jobs_added == 1
    assert result.duplicates == 1
    assert result.errors == 0
    assert len(db.scalars(select(Job)).all()) == 1


def test_database_failure_rolls_back_partial_batch_and_continues() -> None:
    db = database()
    jobs = CompanyAdapterRegistry().enabled_adapters()[0].fetch_jobs()
    # Bypass input validation to exercise a real database NOT NULL failure.
    jobs[1] = jobs[1].model_copy(update={"title": None})
    healthy = CompanyAdapterRegistry().enabled_adapters()[1]
    result = JobIngestionService(db, CompanyAdapterRegistry([adapter_with_jobs(jobs), healthy])).collect_all()
    assert result.errors == 1
    assert result.jobs_added == 5
    assert len(db.scalars(select(Job)).all()) == 5
    runs = db.scalars(select(CollectionRun).order_by(CollectionRun.id)).all()
    assert [run.status for run in runs] == ["failed", "success"]
    assert runs[0].jobs_added == 0
    assert "INSERT" not in runs[0].error_message


def test_commit_failure_is_rolled_back_and_next_company_runs(monkeypatch) -> None:
    db = database()
    original_commit = db.commit
    attempts = 0

    def fail_once() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OperationalError("COMMIT", {}, RuntimeError("test transaction failure"))
        original_commit()

    monkeypatch.setattr(db, "commit", fail_once)
    result = JobIngestionService(db, CompanyAdapterRegistry(CompanyAdapterRegistry().enabled_adapters()[:2])).collect_all()
    assert result.errors == 1
    assert result.jobs_added == 5
    assert len(db.scalars(select(Job)).all()) == 5
    assert [run.status for run in db.scalars(select(CollectionRun).order_by(CollectionRun.id))] == ["failed", "success"]


def test_disabled_company_is_not_fetched_or_recorded(monkeypatch) -> None:
    db = database()
    adapter = CompanyAdapterRegistry().enabled_adapters()[0]
    db.add(Company(name=adapter.get_company(), slug=adapter.slug, careers_url=adapter.careers_url, source_type="MOCK", enabled=False))
    db.commit()

    def forbidden_fetch():
        raise AssertionError("disabled source was fetched")

    monkeypatch.setattr(adapter, "fetch_jobs", forbidden_fetch)
    result = JobIngestionService(db, CompanyAdapterRegistry([adapter])).collect_all()
    assert result.companies_processed == 0
    assert result.errors == 0
    assert db.scalar(select(Job)) is None
    assert db.scalar(select(CollectionRun)) is None


def test_explicit_empty_registry_collects_nothing() -> None:
    result = JobIngestionService(database(), CompanyAdapterRegistry([])).collect_all()
    assert result.companies_processed == 0
