from typing import Literal

from pydantic import BaseModel, Field

EligibilityStatus = Literal["eligible", "ineligible", "unknown"]
ContextStatus = Literal["ready", "no_active_resume", "invalid_active_resume", "ambiguous_active_resume", "insufficient_profile"]


class EligibilityCheck(BaseModel):
    criterion: str
    status: EligibilityStatus = "unknown"
    requirement: str | None = None
    candidate_value: str | None = None
    reason: str


class EligibilityResult(BaseModel):
    status: EligibilityStatus = "unknown"
    checks: list[EligibilityCheck] = Field(default_factory=list)


class MatchComponents(BaseModel):
    skill_overlap: float | None = None
    text_similarity: float | None = None


class MatchWeights(BaseModel):
    skill_overlap: float
    text_similarity: float


class MatchingContext(BaseModel):
    status: ContextStatus
    resume_id: int | None = None
    filename: str | None = None
    explanation: str


class JobMatch(BaseModel):
    status: Literal["scored", "no_active_resume", "invalid_active_resume", "ambiguous_active_resume", "insufficient_profile"]
    resume_id: int | None = None
    score: float | None = None
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    components: MatchComponents = Field(default_factory=MatchComponents)
    weights: MatchWeights
    eligibility: EligibilityResult
    explanation: str
    method: str = "pairwise-tfidf-v1"
