from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Resume, User
from app.schemas.matching import JobMatch, MatchingContext
from app.schemas.resume import ParsedResume
from app.services.matching.engine import MatchingEngine
from app.services.matching.text import resume_text, tokens


class JobMatchingService:
    """Load one active saved profile per request; never persist scores or create users."""

    def __init__(self, db: Session):
        self.engine = MatchingEngine(settings.matching_skill_weight, settings.matching_text_weight)
        self.profile: ParsedResume | None = None
        self.context = MatchingContext(status="no_active_resume", explanation="Review and activate a resume in Resume & Profile to see job matches.")
        active = db.scalars(select(Resume).join(User).where(User.email == settings.development_user_email, Resume.is_active.is_(True)).order_by(Resume.id).limit(2)).all()
        if len(active) > 1:
            self.context = MatchingContext(status="ambiguous_active_resume", explanation="Multiple active resumes exist. Review and activate one resume to resolve this.")
            return
        if not active:
            return
        resume = active[0]
        self.context = MatchingContext(status="invalid_active_resume", resume_id=resume.id, filename=resume.filename, explanation="The active resume has no valid completed profile. Review and activate a successfully parsed resume.")
        if resume.parsing_status != "completed" or resume.parsed_data is None:
            return
        try:
            self.profile = ParsedResume.model_validate(resume.parsed_data)
        except ValidationError:
            return
        if not tokens(resume_text(self.profile)):
            self.context.status = "insufficient_profile"
            self.context.explanation = "The active resume has no saved professional text or skills. Review and save the profile before matching."
            return
        self.context.status = "ready"
        self.context.explanation = "Matching uses the saved profile of your active resume. Save corrections and activate only after review."

    def match(self, title: str, description: str) -> JobMatch:
        return self.engine.match(self.profile, title, description, resume_id=self.context.resume_id, unavailable=self.context.status)
