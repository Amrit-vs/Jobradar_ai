import math

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.resume import ParsedResume
from app.services.matching.engine import MatchingEngine
from app.services.matching.text import cosine_tfidf, extract_skills, resume_text


def test_pairwise_tfidf_has_known_cosine_value() -> None:
    # Shared term idf=1; unique terms idf=log(3/2)+1.
    expected = 1 / (1 + (math.log(1.5) + 1) ** 2)
    assert cosine_tfidf("python docker", "python sql") == pytest.approx(expected)
    assert cosine_tfidf("Python. Python", "python python") == pytest.approx(1)
    assert cosine_tfidf("python", "java") == 0
    assert cosine_tfidf("and the", "python") is None


def test_normalization_preserves_language_boundaries() -> None:
    skills = extract_skills("Python3, ReactJS, Postgres, NodeJS, C++, C#, JavaScript")
    assert skills == {"Python", "React", "PostgreSQL", "Node.js", "C++", "C#", "JavaScript"}
    assert "Java" not in skills
    assert "C" not in skills


def test_exact_score_and_components_are_deterministic() -> None:
    profile = ParsedResume(skills=["Python", "Docker"])
    engine = MatchingEngine()
    result = engine.match(profile, "Python", "Docker", resume_id=7)
    assert result.score == 100
    assert result.components.skill_overlap == 100
    assert result.components.text_similarity == 100
    assert result.matched_skills == ["Docker", "Python"]
    assert result.missing_skills == []
    assert result.eligibility.status == "unknown"
    assert engine.match(profile, "Python", "Docker", resume_id=7) == result


def test_weighted_score_and_skill_coverage() -> None:
    profile = ParsedResume(skills=["Python"])
    engine = MatchingEngine(skill_weight=1, text_weight=0)
    result = engine.match(profile, "Python", "Docker")
    assert result.score == 50
    assert result.matched_skills == ["Python"]
    assert result.missing_skills == ["Docker"]
    assert result.weights.skill_overlap == 1
    assert result.weights.text_similarity == 0


def test_job_without_recognized_skills_renormalizes_available_weights() -> None:
    result = MatchingEngine().match(ParsedResume(certifications=["Bookkeeping"]), "Bookkeeping", "Bookkeeping")
    assert result.score == 100
    assert result.components.skill_overlap is None
    assert result.weights.text_similarity == 1
    assert result.weights.skill_overlap == 0


def test_empty_job_does_not_invent_a_score() -> None:
    result = MatchingEngine().match(ParsedResume(skills=["Python"]), "", "")
    assert result.score is None
    assert result.status == "insufficient_profile"


def test_missing_or_personal_only_profile_does_not_score() -> None:
    engine = MatchingEngine()
    assert engine.match(None, "Python", "Python").status == "no_active_resume"
    profile = ParsedResume(full_name="Python", email="python@example.test", raw_text="Python Docker")
    assert engine.match(profile, "Python", "Docker").score is None
    assert resume_text(profile) == ""


def test_saved_corrections_override_stale_raw_text() -> None:
    profile = ParsedResume(skills=["Java"], raw_text="Python Python Python")
    result = MatchingEngine().match(profile, "Python", "Python")
    assert result.score == 0
    assert result.missing_skills == ["Python"]


def test_projects_and_experience_supply_explicit_professional_skills() -> None:
    profile = ParsedResume.model_validate({"projects": [{"description": "Built FastAPI APIs", "technologies": ["Postgres"]}], "experience": [{"role": "Python Developer"}]})
    result = MatchingEngine().match(profile, "Python", "FastAPI PostgreSQL")
    assert result.components.skill_overlap == 100


@pytest.mark.parametrize("weights", [(0, 0), (-1, 1), (0.5, 2), (float("nan"), 1)])
def test_invalid_weights_are_rejected(weights) -> None:
    with pytest.raises(ValueError):
        MatchingEngine(*weights)


def test_settings_validate_weights_and_optional_resume_values() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, matching_skill_weight=0, matching_text_weight=0)
    with pytest.raises(ValidationError):
        ParsedResume.model_validate({"years_of_experience": -1})
    with pytest.raises(ValidationError):
        ParsedResume.model_validate({"education": [{"percentage": 101}]})
