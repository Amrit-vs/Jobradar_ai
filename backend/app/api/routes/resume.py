from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Resume, User
from app.schemas.resume import ParsedResume, ResumeDetail, ResumeProfileUpdate, ResumeRead
from app.services.resume.extractors import ResumeExtractionError, extractor_for_extension
from app.services.resume.parser import ResumeParser

router = APIRouter(prefix="/resumes", tags=["resumes"])


def development_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == settings.development_user_email))
    if user is None:
        user = User(name=settings.development_user_name, email=settings.development_user_email)
        db.add(user); db.flush()
    return user


def owned_resume(db: Session, resume_id: int) -> Resume:
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == development_user(db).id))
    if resume is None: raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post("/upload", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ResumeDetail:
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}: raise HTTPException(status_code=400, detail="Only PDF and DOCX resume files are supported")
    contents = await file.read()
    if not contents: raise HTTPException(status_code=400, detail="The uploaded document is empty")
    if len(contents) > settings.max_resume_size_mb * 1024 * 1024: raise HTTPException(status_code=413, detail=f"Resume must be at most {settings.max_resume_size_mb} MB")
    resume = Resume(user_id=development_user(db).id, filename=filename, file_type=extension.removeprefix("."), file_size=len(contents), parsing_status="processing")
    db.add(resume); db.flush()
    try:
        text = extractor_for_extension(extension).extract(contents)
        parsed = ResumeParser().parse(text)
        resume.extracted_text = text; resume.parsed_data = parsed.model_dump(); resume.parsing_status = "completed"; resume.parsing_error = None
        db.commit(); db.refresh(resume)
        return ResumeDetail.model_validate(resume).model_copy(update={"parsed_data": parsed})
    except ResumeExtractionError as exc:
        resume.parsing_status = "failed"; resume.parsing_error = str(exc); db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[ResumeRead])
def list_resumes(db: Session = Depends(get_db)) -> list[Resume]:
    return list(db.scalars(select(Resume).where(Resume.user_id == development_user(db).id).order_by(Resume.uploaded_at.desc())))


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeDetail:
    resume = owned_resume(db, resume_id)
    parsed = ParsedResume.model_validate(resume.parsed_data) if resume.parsed_data else None
    return ResumeDetail.model_validate(resume).model_copy(update={"parsed_data": parsed})


@router.get("/{resume_id}/parsed", response_model=ParsedResume)
def get_parsed_resume(resume_id: int, db: Session = Depends(get_db)) -> ParsedResume:
    resume = owned_resume(db, resume_id)
    if not resume.parsed_data: raise HTTPException(status_code=404, detail="Parsed resume data is not available")
    return ParsedResume.model_validate(resume.parsed_data)


@router.put("/{resume_id}/profile", response_model=ResumeDetail)
def update_profile(resume_id: int, profile: ResumeProfileUpdate, db: Session = Depends(get_db)) -> ResumeDetail:
    resume = owned_resume(db, resume_id); resume.parsed_data = profile.model_dump(); db.commit(); db.refresh(resume)
    return ResumeDetail.model_validate(resume).model_copy(update={"parsed_data": profile})


@router.post("/{resume_id}/activate", response_model=ResumeRead)
def activate_resume(resume_id: int, db: Session = Depends(get_db)) -> Resume:
    resume = owned_resume(db, resume_id)
    db.execute(update(Resume).where(Resume.user_id == resume.user_id).values(is_active=False))
    resume.is_active = True; db.commit(); db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: int, db: Session = Depends(get_db)) -> None:
    resume = owned_resume(db, resume_id); db.delete(resume); db.commit()
