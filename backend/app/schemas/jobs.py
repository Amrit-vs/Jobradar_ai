from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NormalizedJob(BaseModel):
    """The source-independent job representation accepted by ingestion."""

    external_job_id: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    url: str = Field(min_length=1, max_length=2048)
    posted_at: datetime | None = None
    employment_type: str | None = Field(default=None, max_length=80)
    experience_level: str | None = Field(default=None, max_length=80)
    source: str = Field(min_length=1, max_length=120)


class JobRead(BaseModel):
    id: int
    company: str
    company_slug: str
    title: str
    description: str
    location: str | None
    country: str | None
    city: str | None
    url: str
    posted_at: datetime | None
    employment_type: str | None
    experience_level: str | None
    source: str
    status: str
    freshness: str

    model_config = ConfigDict(from_attributes=True)

