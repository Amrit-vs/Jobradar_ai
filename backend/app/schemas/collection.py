from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CollectionStats(BaseModel):
    companies_processed: int = 0
    jobs_fetched: int = 0
    jobs_added: int = 0
    jobs_updated: int = 0
    duplicates: int = 0
    errors: int = 0


class CollectionRunRead(BaseModel):
    id: int
    company_id: int
    company: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    jobs_fetched: int
    jobs_added: int
    jobs_updated: int
    duplicates: int
    errors: int
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)

