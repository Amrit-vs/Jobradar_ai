from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import CollectionRun
from app.schemas.collection import CollectionRunRead, CollectionStats
from app.services.ingestion import JobIngestionService

router = APIRouter(prefix="/admin", tags=["collection"])


@router.post("/collect", response_model=CollectionStats)
def collect_mock_jobs(db: Session = Depends(get_db)) -> CollectionStats:
    return JobIngestionService(db).collect_all()


@router.get("/collection-runs", response_model=list[CollectionRunRead])
def collection_runs(db: Session = Depends(get_db)) -> list[CollectionRunRead]:
    runs = db.scalars(select(CollectionRun).options(joinedload(CollectionRun.company)).order_by(CollectionRun.started_at.desc())).unique()
    return [CollectionRunRead(id=run.id, company_id=run.company_id, company=run.company.name, started_at=run.started_at, completed_at=run.completed_at, status=run.status, jobs_fetched=run.jobs_fetched, jobs_added=run.jobs_added, jobs_updated=run.jobs_updated, duplicates=run.duplicates, errors=run.errors, error_message=run.error_message) for run in runs]

