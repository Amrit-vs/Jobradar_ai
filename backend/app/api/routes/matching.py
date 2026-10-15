from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.matching import MatchingContext
from app.services.matching.service import JobMatchingService

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/context", response_model=MatchingContext)
def matching_context(db: Session = Depends(get_db)) -> MatchingContext:
    return JobMatchingService(db).context
