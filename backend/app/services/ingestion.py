import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CollectionRun, Company, Job
from app.schemas.collection import CollectionStats
from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.registry import CompanyAdapterRegistry
from app.services.freshness import classify_freshness, job_status_for_freshness

logger = logging.getLogger(__name__)


class JobIngestionService:
    def __init__(self, db: Session, registry: CompanyAdapterRegistry | None = None):
        self.db = db
        self.registry = registry or CompanyAdapterRegistry()

    def collect_all(self) -> CollectionStats:
        total = CollectionStats()
        for adapter in self.registry.enabled_adapters():
            run_stats = self._collect_adapter(adapter)
            if run_stats is None:
                continue
            total.companies_processed += 1
            for field in ("jobs_fetched", "jobs_added", "jobs_updated", "duplicates", "errors"):
                setattr(total, field, getattr(total, field) + getattr(run_stats, field))
        logger.info("collection_completed companies=%s fetched=%s added=%s updated=%s duplicates=%s errors=%s", total.companies_processed, total.jobs_fetched, total.jobs_added, total.jobs_updated, total.duplicates, total.errors)
        return total

    def _company_for(self, adapter: JobSourceAdapter) -> Company:
        company = self.db.scalar(select(Company).where(Company.slug == adapter.slug))
        if company is None:
            company = Company(name=adapter.get_company(), slug=adapter.slug, careers_url=adapter.careers_url, source_type=adapter.source_type, enabled=True)
            self.db.add(company)
            self.db.flush()
        return company

    def _collect_adapter(self, adapter: JobSourceAdapter) -> CollectionStats | None:
        """Own one transaction per source; failed batches never persist partial jobs."""
        stats = CollectionStats()
        try:
            company = self._company_for(adapter)
            if not company.enabled:
                return None
            run = CollectionRun(company_id=company.id, status="running")
            self.db.add(run)
            self.db.flush()
            logger.info("adapter_started company=%s", adapter.slug)
            jobs = adapter.fetch_jobs()
            stats.jobs_fetched = len(jobs)
            for normalized_job in jobs:
                added, updated, duplicate = self._upsert(company, normalized_job)
                stats.jobs_added += added
                stats.jobs_updated += updated
                stats.duplicates += duplicate
                # Make this record visible to the next lookup with autoflush disabled,
                # and detect constraint failures inside the source transaction.
                self.db.flush()
            run.status = "success"
            self._finish_run(run, stats)
            self.db.commit()
            logger.info("adapter_completed company=%s fetched=%s added=%s updated=%s duplicates=%s", adapter.slug, stats.jobs_fetched, stats.jobs_added, stats.jobs_updated, stats.duplicates)
        except Exception as exc:  # one source must not stop the rest of the collection
            self.db.rollback()
            logger.error("adapter_failed company=%s error_type=%s", adapter.slug, type(exc).__name__)
            stats = CollectionStats(jobs_fetched=stats.jobs_fetched, errors=1)
            try:
                company = self._company_for(adapter)
                run = CollectionRun(company_id=company.id, status="failed", error_message=f"Collection failed ({type(exc).__name__})")
                self.db.add(run)
                self._finish_run(run, stats)
                self.db.commit()
            except Exception:
                # A database outage may also prevent writing failure history.
                self.db.rollback()
                logger.error("collection_failure_history_unavailable company=%s", adapter.slug)
        return stats

    @staticmethod
    def _finish_run(run: CollectionRun, stats: CollectionStats) -> None:
        run.jobs_fetched = stats.jobs_fetched
        run.jobs_added = stats.jobs_added
        run.jobs_updated = stats.jobs_updated
        run.duplicates = stats.duplicates
        run.errors = stats.errors
        run.completed_at = datetime.now(timezone.utc)

    def _upsert(self, company: Company, incoming: NormalizedJob) -> tuple[int, int, int]:
        existing = self.db.scalar(select(Job).where(Job.company_id == company.id, Job.external_job_id == incoming.external_job_id))
        if existing is None:
            existing = self.db.scalar(select(Job).where(
                Job.company_id == company.id,
                Job.title == incoming.title,
                Job.location == incoming.location,
                Job.url == incoming.url,
            ))
        now = datetime.now(timezone.utc)
        freshness = classify_freshness(incoming.posted_at, now)
        if existing is None:
            self.db.add(Job(company_id=company.id, external_job_id=incoming.external_job_id, title=incoming.title, description=incoming.description, location=incoming.location, country=incoming.country, city=incoming.city, url=incoming.url, employment_type=incoming.employment_type, experience_level=incoming.experience_level, posted_at=incoming.posted_at, first_seen_at=now, last_seen_at=now, source=incoming.source, status=job_status_for_freshness(freshness)))
            return 1, 0, 0
        changes = False
        for field in ("title", "description", "location", "country", "city", "url", "employment_type", "experience_level", "posted_at", "source"):
            value = getattr(incoming, field)
            if not self._equal_field_values(getattr(existing, field), value):
                setattr(existing, field, value)
                changes = True
        new_status = job_status_for_freshness(freshness)
        if existing.status != new_status:
            existing.status = new_status
        existing.last_seen_at = now
        return (0, 1, 0) if changes else (0, 0, 1)

    @staticmethod
    def _equal_field_values(existing: object, incoming: object) -> bool:
        """Compare timestamps as the same UTC instant across PostgreSQL and SQLite tests."""
        if isinstance(existing, datetime) and isinstance(incoming, datetime):
            existing_utc = existing.replace(tzinfo=timezone.utc) if existing.tzinfo is None else existing.astimezone(timezone.utc)
            incoming_utc = incoming.replace(tzinfo=timezone.utc) if incoming.tzinfo is None else incoming.astimezone(timezone.utc)
            return existing_utc == incoming_utc
        return existing == incoming
