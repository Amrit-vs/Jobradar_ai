import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Resume, User
from test_api_resume import resume_client, upload


def prepare(client):
    assert client.post("/api/admin/collect").json()["jobs_added"] == 25
    resume_id = upload(client).json()["id"]
    profile = {"skills": ["Python"], "years_of_experience": 2, "education": [{"degree": "B.Tech", "graduation_year": "2026", "percentage": 75}], "raw_text": "STALE Java"}
    assert client.put(f"/api/resumes/{resume_id}/profile", json=profile).status_code == 200
    assert client.post(f"/api/resumes/{resume_id}/activate").status_code == 200
    return resume_id


def test_no_active_resume_preserves_jobs_and_does_not_create_user(resume_client) -> None:
    client, engine = resume_client
    assert client.get("/api/matching/context").json()["status"] == "no_active_resume"
    with Session(engine) as db:
        assert db.scalar(select(User)) is None
    assert client.post("/api/admin/collect").status_code == 200
    jobs = client.get("/api/jobs").json()
    assert len(jobs) == 25
    assert all(job["match_score"] is None and job["matching"]["status"] == "no_active_resume" for job in jobs)
    assert client.get("/api/jobs", params={"min_match_score": 0}).json() == []


def test_scores_ranking_filtering_and_detail_are_consistent(resume_client) -> None:
    client, _ = resume_client
    resume_id = prepare(client)
    assert client.get("/api/matching/context").json()["resume_id"] == resume_id
    jobs = client.get("/api/jobs", params={"sort_by": "match_score"}).json()
    scores = [job["match_score"] for job in jobs]
    assert scores == sorted(scores, reverse=True)
    assert max(scores) > min(scores)
    filtered = client.get("/api/jobs", params={"sort_by": "match_score", "min_match_score": max(scores)}).json()
    assert 0 < len(filtered) < 25
    assert all(job["match_score"] >= max(scores) for job in filtered)
    for job in jobs:
        detail = client.get(f"/api/jobs/{job['id']}").json()
        assert detail["matching"] == job["matching"]
        assert detail["match_score"] == job["match_score"]
        assert 0 <= detail["match_score"] <= 100
    company = jobs[0]["company_slug"]
    subset = client.get("/api/jobs", params={"company": company}).json()
    original = {job["id"]: job["match_score"] for job in jobs}
    assert all(job["match_score"] == original[job["id"]] for job in subset)
    assert client.get("/api/jobs", params={"sort_by": "match_score"}).json() == jobs


def test_saved_edits_activation_and_deletion_change_matching_immediately(resume_client, monkeypatch) -> None:
    client, _ = resume_client
    monkeypatch.setattr(settings, "matching_skill_weight", 1)
    monkeypatch.setattr(settings, "matching_text_weight", 0)
    first_id = prepare(client)
    jobs = client.get("/api/jobs").json()
    python_job = next(job for job in jobs if "Python" in job["matching"]["matched_skills"] and "Java" not in job["description"])
    assert python_job["match_score"] > 0
    assert client.put(f"/api/resumes/{first_id}/profile", json={"skills": ["Java"], "raw_text": "Python"}).status_code == 200
    assert client.get(f"/api/jobs/{python_job['id']}").json()["match_score"] == 0
    second_id = upload(client).json()["id"]
    assert client.put(f"/api/resumes/{second_id}/profile", json={"skills": ["Python"]}).status_code == 200
    # An inactive upload does not replace the selected resume.
    assert client.get(f"/api/jobs/{python_job['id']}").json()["match_score"] == 0
    assert client.post(f"/api/resumes/{second_id}/activate").status_code == 200
    assert client.get(f"/api/jobs/{python_job['id']}").json()["match_score"] > 0
    assert client.delete(f"/api/resumes/{second_id}").status_code == 204
    assert client.get("/api/matching/context").json()["status"] == "no_active_resume"


@pytest.mark.parametrize(("parsed", "status", "expected"), [(None, "failed", "invalid_active_resume"), ({"skills": 123}, "completed", "invalid_active_resume"), ({}, "completed", "insufficient_profile")])
def test_unusable_active_profile_is_explained(resume_client, parsed, status, expected) -> None:
    client, engine = resume_client
    resume_id = prepare(client)
    with Session(engine) as db:
        resume = db.get(Resume, resume_id)
        resume.parsed_data = parsed
        resume.parsing_status = status
        db.commit()
    assert client.get("/api/matching/context").json()["status"] == expected
    jobs = client.get("/api/jobs").json()
    assert all(job["matching"]["status"] == expected and job["match_score"] is None for job in jobs)


def test_multiple_active_resumes_fail_closed_until_reactivated(resume_client) -> None:
    client, engine = resume_client
    first_id = prepare(client)
    second_id = upload(client).json()["id"]
    with Session(engine) as db:
        db.get(Resume, second_id).is_active = True
        db.commit()
    assert client.get("/api/matching/context").json()["status"] == "ambiguous_active_resume"
    assert all(job["match_score"] is None for job in client.get("/api/jobs").json())
    assert client.post(f"/api/resumes/{first_id}/activate").status_code == 200
    assert client.get("/api/matching/context").json()["status"] == "ready"


def test_another_users_active_resume_is_never_used(resume_client) -> None:
    client, engine = resume_client
    with Session(engine) as db:
        user = User(name="Other", email="other@example.test")
        db.add(user)
        db.flush()
        db.add(Resume(user_id=user.id, filename="private.pdf", file_type="pdf", is_active=True, parsing_status="completed", parsed_data={"skills": ["Python"]}))
        db.commit()
    assert client.get("/api/matching/context").json()["status"] == "no_active_resume"


@pytest.mark.parametrize("params", [{"min_match_score": -1}, {"min_match_score": 101}, {"sort_by": "unsupported"}])
def test_invalid_matching_filters_are_rejected(resume_client, params) -> None:
    client, _ = resume_client
    assert client.get("/api/jobs", params=params).status_code == 422
