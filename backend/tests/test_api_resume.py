import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.resume import upload_resume
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Resume, User
from test_resume_extractors import docx_bytes, pdf_bytes


@pytest.fixture
def resume_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override():
        with Session(engine, autoflush=False) as db:
            yield db

    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            yield client, engine
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def upload(client, contents=None, filename="resume.docx"):
    return client.post("/api/resumes/upload", files={"file": (filename, contents if contents is not None else docx_bytes())})


def test_resume_lifecycle_preserves_edits_and_switches_active_resume(resume_client) -> None:
    client, _ = resume_client
    first = upload(client)
    assert first.status_code == 201
    first_id = first.json()["id"]
    assert first.json()["parsing_status"] == "completed"
    assert "Python" in first.json()["parsed_data"]["skills"]
    assert client.get(f"/api/resumes/{first_id}/parsed").status_code == 200
    profile = first.json()["parsed_data"]
    profile["full_name"] = "Reviewed Candidate"
    profile["skills"] = ["Rust"]
    assert client.put(f"/api/resumes/{first_id}/profile", json=profile).status_code == 200
    assert client.get(f"/api/resumes/{first_id}").json()["parsed_data"] == profile
    second = upload(client, pdf_bytes(), "second.pdf")
    assert second.status_code == 201
    second_id = second.json()["id"]
    assert client.post(f"/api/resumes/{first_id}/activate").json()["is_active"] is True
    assert client.post(f"/api/resumes/{first_id}/activate").json()["is_active"] is True
    assert client.post(f"/api/resumes/{second_id}/activate").json()["is_active"] is True
    active = [resume["id"] for resume in client.get("/api/resumes").json() if resume["is_active"]]
    assert active == [second_id]
    assert client.delete(f"/api/resumes/{second_id}").status_code == 204
    assert client.get(f"/api/resumes/{second_id}").status_code == 404
    assert client.get(f"/api/resumes/{first_id}/parsed").json()["skills"] == ["Rust"]


def test_failed_resume_is_saved_and_can_be_deleted(resume_client) -> None:
    client, _ = resume_client
    assert upload(client, b"invalid", "broken.pdf").status_code == 400
    failed = client.get("/api/resumes").json()[0]
    assert failed["parsing_status"] == "failed"
    assert failed["parsing_error"]
    assert client.get(f"/api/resumes/{failed['id']}/parsed").status_code == 404
    assert client.delete(f"/api/resumes/{failed['id']}").status_code == 204
    assert client.get("/api/resumes").json() == []


@pytest.mark.parametrize(("filename", "contents", "status"), [("resume.txt", b"text", 400), ("resume.pdf", b"", 400), ("resume.docx", b"invalid", 400)])
def test_upload_validation(resume_client, filename, contents, status) -> None:
    client, _ = resume_client
    assert upload(client, contents, filename).status_code == status


def test_oversized_upload_returns_413_without_creating_resume(resume_client, monkeypatch) -> None:
    client, _ = resume_client
    monkeypatch.setattr(settings, "max_resume_size_mb", 1)
    assert upload(client, b"x" * (1024 * 1024 + 1)).status_code == 413
    assert client.get("/api/resumes").json() == []


def test_upload_read_is_bounded(monkeypatch) -> None:
    monkeypatch.setattr(settings, "max_resume_size_mb", 1)
    file = AsyncMock(spec=UploadFile)
    file.filename = "resume.pdf"
    file.read.return_value = b"x" * (1024 * 1024 + 1)
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload_resume(file=file, db=None))
    assert error.value.status_code == 413
    file.read.assert_awaited_once_with(1024 * 1024 + 1)


def test_resume_endpoints_do_not_expose_another_users_resume(resume_client) -> None:
    client, engine = resume_client
    with Session(engine) as db:
        user = User(name="Other", email="other@example.test")
        db.add(user)
        db.flush()
        resume = Resume(user_id=user.id, filename="private.pdf", file_type="pdf")
        db.add(resume)
        db.commit()
        resume_id = resume.id
    assert client.get("/api/resumes").json() == []
    assert client.get(f"/api/resumes/{resume_id}").status_code == 404
    assert client.put(f"/api/resumes/{resume_id}/profile", json={}).status_code == 404
    assert client.post(f"/api/resumes/{resume_id}/activate").status_code == 404
    assert client.delete(f"/api/resumes/{resume_id}").status_code == 404
