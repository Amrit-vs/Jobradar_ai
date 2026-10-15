"""Opt-in PostgreSQL test: run only against an explicitly disposable database."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models import Resume, User


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires disposable PostgreSQL")
def test_concurrent_activation_serializes_per_user(monkeypatch) -> None:
    if os.getenv("TEST_DATABASE_DISPOSABLE") != "1":
        pytest.fail("Set TEST_DATABASE_DISPOSABLE=1 only for an isolated disposable database")
    engine = create_engine(os.environ["TEST_POSTGRES_URL"])
    email = f"activation-{uuid4().hex}@example.test"
    monkeypatch.setattr(settings, "development_user_email", email)
    with Session(engine) as db:
        user = User(name="Concurrent Candidate", email=email)
        db.add(user)
        db.flush()
        user_id = user.id
        resumes = [Resume(user_id=user_id, filename=f"{index}.pdf", file_type="pdf", parsing_status="completed") for index in range(2)]
        db.add_all(resumes)
        db.flush()
        ids = [resume.id for resume in resumes]
        db.commit()

    def override():
        with Session(engine, autoflush=False) as db:
            yield db

    app.dependency_overrides[get_db] = override
    waiting = Event()
    guard = Lock()
    attempts = 0

    def observe_lock(connection, cursor, statement, parameters, context, executemany):
        nonlocal attempts
        if "FOR UPDATE" in statement:
            with guard:
                attempts += 1
                if attempts == 2:
                    waiting.set()

    def activate(resume_id):
        with TestClient(app) as client:
            return client.post(f"/api/resumes/{resume_id}/activate")

    try:
        # Hold the user lock so both HTTP requests must wait, then release together.
        with ThreadPoolExecutor(max_workers=2) as pool:
            with Session(engine) as blocker:
                blocker.scalar(select(User).where(User.id == user_id).with_for_update())
                event.listen(engine, "before_cursor_execute", observe_lock)
                futures = [pool.submit(activate, resume_id) for resume_id in ids]
                try:
                    assert waiting.wait(10), "both activation requests must acquire the user row lock"
                    assert all(not future.done() for future in futures)
                finally:
                    blocker.rollback()
                responses = [future.result(timeout=10) for future in futures]
        assert [response.status_code for response in responses] == [200, 200]
        with Session(engine) as db:
            active = db.scalars(select(Resume.id).where(Resume.user_id == user_id, Resume.is_active.is_(True))).all()
            assert len(active) == 1
            assert active[0] in ids
    finally:
        event.remove(engine, "before_cursor_execute", observe_lock)
        app.dependency_overrides.pop(get_db, None)
        # Remove only records created by this test, never truncate shared tables.
        with Session(engine) as db:
            db.delete(db.get(User, user_id))
            db.commit()
        engine.dispose()
