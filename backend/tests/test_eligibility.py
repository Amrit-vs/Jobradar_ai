import pytest

from app.schemas.resume import ParsedResume
from app.services.matching.eligibility import evaluate_eligibility
from app.services.matching.engine import MatchingEngine

REQUIREMENTS = "Required graduation year: 2026\nRequired degree: B.Tech or B.E.\nMinimum experience: 2 years\nMinimum academic percentage: 60%"


def candidate(**updates):
    return ParsedResume.model_validate({"years_of_experience": 2, "education": [{"degree": "Bachelor of Technology in Computer Science", "graduation_year": "2026", "percentage": 70}], **updates})


def test_explicit_criteria_are_eligible_with_reasons() -> None:
    result = evaluate_eligibility(candidate(), REQUIREMENTS)
    assert result.status == "eligible"
    assert len(result.checks) == 4
    assert all(check.status == "eligible" and check.reason and check.requirement for check in result.checks)


@pytest.mark.parametrize("requirement", ["Required graduation year: 2025", "Required degree: M.Tech", "Minimum experience: 3 years", "Minimum academic percentage: 80%"])
def test_confirmed_failure_is_ineligible(requirement) -> None:
    assert evaluate_eligibility(candidate(), requirement).status == "ineligible"


def test_missing_candidate_data_cgpa_and_dates_do_not_invent_eligibility() -> None:
    profile = ParsedResume.model_validate({"education": [{"cgpa": "9/10"}], "experience": [{"start_date": "2020", "end_date": "2026"}]})
    result = evaluate_eligibility(profile, REQUIREMENTS)
    assert result.status == "unknown"
    assert all(check.status == "unknown" for check in result.checks)
    assert evaluate_eligibility(None, REQUIREMENTS).status == "unknown"


@pytest.mark.parametrize("description", ["New Grad; 0–2 years; strong academics", "Bachelor's preferred, graduation around 2026", "Required degree: Bachelor's or equivalent", "Required degree: Bachelor's in Computer Science", "Minimum experience: 2-5 years", "Minimum academic percentage: 9/10", "Required graduation year: 2026; Required graduation year: 2027"])
def test_ambiguous_or_unsupported_requirements_are_unknown(description) -> None:
    assert evaluate_eligibility(candidate(), description).status == "unknown"


def test_education_requirements_cannot_be_combined_across_degrees() -> None:
    profile = candidate(education=[{"degree": "B.Tech", "graduation_year": "2024", "percentage": 80}, {"degree": "M.Tech", "graduation_year": "2026", "percentage": 80}])
    assert evaluate_eligibility(profile, REQUIREMENTS).status == "ineligible"


def test_unknown_alternative_qualification_prevents_false_rejection() -> None:
    profile = candidate(education=[{"degree": "M.Tech"}, {"degree": "B.Tech"}])
    assert evaluate_eligibility(profile, REQUIREMENTS).status == "unknown"


def test_multiple_qualifications_can_satisfy_requirements_without_cross_mixing() -> None:
    profile = candidate(education=[{"degree": "M.Tech", "graduation_year": "2024"}, {"degree": "B.E.", "graduation_year": "2026", "percentage": 65}])
    assert evaluate_eligibility(profile, REQUIREMENTS).status == "eligible"


def test_year_range_and_generic_degree_requirement() -> None:
    assert evaluate_eligibility(candidate(), "Required graduation years: 2025-2027; Required degree: Bachelor's degree").status == "eligible"
    assert evaluate_eligibility(candidate(), "Required graduation years: 2025 or 2026").status == "eligible"


def test_generic_candidate_degree_does_not_prove_a_specific_degree_mismatch() -> None:
    profile = candidate(education=[{"degree": "Bachelor's degree"}])
    assert evaluate_eligibility(profile, "Required degree: B.Tech").status == "unknown"


def test_eligibility_never_changes_match_score() -> None:
    engine = MatchingEngine(skill_weight=1, text_weight=0)
    qualified = engine.match(candidate(skills=["Python"]), "Python", "Python\nMinimum experience: 2 years")
    unqualified = engine.match(candidate(skills=["Python"], years_of_experience=0), "Python", "Python\nMinimum experience: 2 years")
    assert qualified.score == unqualified.score == 100
    assert qualified.eligibility.status == "eligible"
    assert unqualified.eligibility.status == "ineligible"
