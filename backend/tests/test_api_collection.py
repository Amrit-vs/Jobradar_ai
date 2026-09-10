from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


def test_collection_and_job_endpoints() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    try:
        client = TestClient(app)
        result = client.post("/api/admin/collect")
        assert result.status_code == 200
        assert result.json()["jobs_added"] == 25
        jobs = client.get("/api/jobs", params={"company": "google", "posted_within_days": 30})
        assert jobs.status_code == 200
        assert len(jobs.json()) == 5
        job = client.get(f"/api/jobs/{jobs.json()[0]['id']}")
        assert job.status_code == 200
        assert job.json()["source"] == "MOCK"
        assert len(client.get("/api/companies").json()) == 5
        assert len(client.get("/api/admin/collection-runs").json()) == 5
    finally:
        app.dependency_overrides.clear()
