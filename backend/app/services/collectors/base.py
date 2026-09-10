from abc import ABC, abstractmethod

from app.schemas.jobs import NormalizedJob


class JobSourceAdapter(ABC):
    """A safe interface for company sources. Phase 2 implementations are offline mocks."""

    slug: str
    careers_url: str
    source_type = "MOCK"

    @abstractmethod
    def get_company(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_jobs(self) -> list[NormalizedJob]:
        raise NotImplementedError

