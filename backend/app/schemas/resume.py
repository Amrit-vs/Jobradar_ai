from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    graduation_year: str | None = None
    cgpa: str | None = None


class ExperienceEntry(BaseModel):
    company: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class ProjectEntry(BaseModel):
    name: str | None = None
    organization: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    raw_text: str = ""


class ResumeRead(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime
    updated_at: datetime
    parsing_status: str
    parsing_error: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ResumeDetail(ResumeRead):
    parsed_data: ParsedResume | None = None


class ResumeProfileUpdate(ParsedResume):
    raw_text: str = ""
