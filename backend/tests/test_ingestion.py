from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import CollectionRun, Job
from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.registry import CompanyAdapterRegistry
from app.services.ingestion import JobIngestionService


def database() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


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
