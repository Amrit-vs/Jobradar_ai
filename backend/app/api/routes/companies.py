from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import CollectionRun, Company, Job
from app.schemas.common import CompanyRead

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)) -> list[CompanyRead]:
    companies = db.scalars(select(Company).order_by(Company.name)).all()
    payload: list[CompanyRead] = []
    for company in companies:
        latest_run = db.scalar(select(CollectionRun).where(CollectionRun.company_id == company.id).order_by(CollectionRun.started_at.desc()))
        base = CompanyRead.model_validate(company)
        payload.append(base.model_copy(update={"job_count": db.scalar(select(func.count(Job.id)).where(Job.company_id == company.id)) or 0, "last_collection_status": latest_run.status if latest_run else None, "last_collection_at": latest_run.completed_at if latest_run else None}))
    return payload
