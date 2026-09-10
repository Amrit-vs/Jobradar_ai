from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    education: Mapped[str | None] = mapped_column(Text)
    degree: Mapped[str | None] = mapped_column(String(255))
    graduation_year: Mapped[int | None]
    years_of_experience: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_experience_levels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_companies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    user: Mapped[User] = relationship(back_populates="profile")

