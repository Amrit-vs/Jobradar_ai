from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str


class CompanyRead(BaseModel):
    id: int
    name: str
    slug: str
    careers_url: str
    source_type: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    job_count: int = 0
    last_collection_status: str | None = None
    last_collection_at: datetime | None = None

    model_config = {"from_attributes": True}
