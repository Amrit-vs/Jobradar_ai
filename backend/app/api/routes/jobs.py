from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Job
from app.schemas.jobs import JobRead
from app.services.freshness import classify_freshness

router = APIRouter(prefix="/jobs", tags=["jobs"])


def serialize(job: Job) -> JobRead:
    return JobRead(id=job.id, company=job.company.name, company_slug=job.company.slug, title=job.title, description=job.description, location=job.location, country=job.country, city=job.city, url=job.url, posted_at=job.posted_at, employment_type=job.employment_type, experience_level=job.experience_level, source=job.source, status=job.status, freshness=classify_freshness(job.posted_at))


@router.get("", response_model=list[JobRead])
def list_jobs(company: str | None = None, location: str | None = None, title: str | None = None, experience_level: str | None = None, min_match_score: float | None = Query(default=None, ge=0, le=100), posted_within_days: int | None = Query(default=None, ge=0), status: str | None = None, db: Session = Depends(get_db)) -> list[JobRead]:
    query = select(Job).options(joinedload(Job.company)).order_by(Job.posted_at.desc())
    if company:
        query = query.where((Job.company.has(name=company)) | (Job.company.has(slug=company.lower())))
    if location: query = query.where(Job.location.ilike(f"%{location}%"))
    if title: query = query.where(Job.title.ilike(f"%{title}%"))
    if experience_level: query = query.where(Job.experience_level == experience_level)
    if posted_within_days is not None: query = query.where(Job.posted_at >= datetime.now(timezone.utc) - timedelta(days=posted_within_days))
    if status: query = query.where(Job.status == status.upper())
    # min_match_score is accepted for forward-compatible clients; Phase 5 supplies its data.
    _ = min_match_score
    return [serialize(job) for job in db.scalars(query).unique()]


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobRead:
    job = db.scalar(select(Job).options(joinedload(Job.company)).where(Job.id == job_id))
    if job is None: raise HTTPException(status_code=404, detail="Job not found")
    return serialize(job)

