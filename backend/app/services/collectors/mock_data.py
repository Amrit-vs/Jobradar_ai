from datetime import datetime, timedelta, timezone

from app.schemas.jobs import NormalizedJob


def mock_jobs(company: str, slug: str, roles: list[tuple[str, str, str, str]], prefix: str) -> list[NormalizedJob]:
    """Build deterministic, realistic offline records with varied freshness and requirements."""
    # Stable within a day so repeat collection tests exercise deduplication, not clock noise.
    now = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
    jobs: list[NormalizedJob] = []
    for index, (title, location, level, skills) in enumerate(roles, start=1):
        city, country = (location.split(", ", 1) + [None])[:2] if ", " in location else (location, None)
        jobs.append(NormalizedJob(
            external_job_id=f"{prefix}-MOCK-{index:03d}", company=company, title=title,
            description=f"MOCK JOB — {title} at {company}. Required skills: {skills}. Work with an inclusive engineering team to build reliable products.",
            location=location, city=city, country=country, url=f"https://example.invalid/jobradar/{slug}/{index}",
            posted_at=now - timedelta(hours=(index - 1) * 35), employment_type="Full-time" if "Intern" not in title else "Internship",
            experience_level=level, source="MOCK",
        ))
    return jobs
