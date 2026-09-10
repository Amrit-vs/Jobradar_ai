import pytest
from pydantic import ValidationError

from app.schemas.jobs import NormalizedJob
from app.services.collectors.registry import CompanyAdapterRegistry


def test_registry_exposes_five_mock_adapters() -> None:
    adapters = CompanyAdapterRegistry().enabled_adapters()
    assert [adapter.get_company() for adapter in adapters] == ["Google", "Microsoft", "Amazon", "NVIDIA", "Adobe"]
    assert sum(len(adapter.fetch_jobs()) for adapter in adapters) == 25
    assert all(job.source == "MOCK" for adapter in adapters for job in adapter.fetch_jobs())


def test_normalized_job_rejects_invalid_input() -> None:
    with pytest.raises(ValidationError):
        NormalizedJob(external_job_id="", company="Google", title="", description="", url="", source="MOCK")

