from dataclasses import dataclass

from app.schemas.matching import JobMatch, MatchComponents, MatchWeights
from app.schemas.resume import ParsedResume
from app.services.matching.eligibility import evaluate_eligibility
from app.services.matching.text import cosine_tfidf, extract_skills, normalize_skill, resume_text, tokens


@dataclass(frozen=True)
class MatchingEngine:
    skill_weight: float = 0.6
    text_weight: float = 0.4

    def __post_init__(self) -> None:
        if not (0 <= self.skill_weight <= 1 and 0 <= self.text_weight <= 1 and self.skill_weight + self.text_weight > 0):
            raise ValueError("Matching weights must be finite, in [0, 1], and have a positive sum")

    def match(self, profile: ParsedResume | None, title: str, description: str, *, resume_id: int | None = None, unavailable: str = "no_active_resume") -> JobMatch:
        result = JobMatch(
            status=unavailable if profile is None else "insufficient_profile",
            resume_id=resume_id,
            weights=MatchWeights(skill_overlap=0, text_similarity=0),
            eligibility=evaluate_eligibility(profile, description),
            explanation="Select an active, reviewed resume in Resume & Profile to see matching scores.",
        )
        if profile is None:
            if unavailable != "no_active_resume":
                result.explanation = "The active resume is unavailable or ambiguous. Review and activate one successfully parsed resume."
            return result
        candidate_text = resume_text(profile)
        if not tokens(candidate_text):
            result.explanation = "The active resume has no saved professional text or skills to compare. Review and save the profile."
            return result
        job_text = f"{title}\n{description}"
        candidate_skills = extract_skills(candidate_text) | {normalize_skill(skill) for skill in profile.skills if skill.strip()}
        job_skills = extract_skills(job_text)
        matched = sorted(candidate_skills & job_skills, key=str.casefold)
        missing = sorted(job_skills - candidate_skills, key=str.casefold)
        skill_score = len(matched) / len(job_skills) if job_skills else None
        text_score = cosine_tfidf(candidate_text, job_text)
        active_skill = self.skill_weight if skill_score is not None else 0
        active_text = self.text_weight if text_score is not None else 0
        total = active_skill + active_text
        result.matched_skills = matched
        result.missing_skills = missing
        result.components = MatchComponents(skill_overlap=round(skill_score * 100, 2) if skill_score is not None else None, text_similarity=round(text_score * 100, 2) if text_score is not None else None)
        if not total:
            result.explanation = "No configured scoring component has sufficient data for comparison."
            return result
        result.weights = MatchWeights(skill_overlap=active_skill / total, text_similarity=active_text / total)
        result.score = round(100 * ((skill_score or 0) * active_skill + (text_score or 0) * active_text) / total, 2)
        result.status = "scored"
        result.explanation = f"{len(matched)} of {len(job_skills)} recognized job skills matched. Score combines skill coverage and pairwise TF-IDF cosine similarity using the effective weights shown. Eligibility is evaluated separately; missing skills are mentions, not inferred hard requirements."
        return result
