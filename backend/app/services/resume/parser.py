import re

from app.schemas.resume import EducationEntry, ExperienceEntry, ParsedResume, ProjectEntry

SKILL_ALIASES = {"python": "Python", "python3": "Python", "java": "Java", "c": "C", "c++": "C++", "javascript": "JavaScript", "typescript": "TypeScript", "sql": "SQL", "react": "React", "reactjs": "React", "node.js": "Node.js", "nodejs": "Node.js", "express": "Express", "fastapi": "FastAPI", "django": "Django", "docker": "Docker", "git": "Git", "github": "GitHub", "postgres": "PostgreSQL", "postgresql": "PostgreSQL", "mongodb": "MongoDB", "mysql": "MySQL", "tensorflow": "TensorFlow", "tensor flow": "TensorFlow", "pytorch": "PyTorch", "opencv": "OpenCV", "machine learning": "Machine Learning", "deep learning": "Deep Learning", "nlp": "NLP", "computer vision": "Computer Vision", "aws": "AWS", "azure": "Azure", "gcp": "GCP", "kubernetes": "Kubernetes"}
SECTION_NAMES = {"education": "education", "academic background": "education", "technical skills": "skills", "skills": "skills", "work experience": "experience", "professional experience": "experience", "experience": "experience", "experience and leadership": "experience", "internships": "experience", "internship experience": "experience", "technical projects": "projects", "projects": "projects", "personal projects": "projects", "academic projects": "projects", "certifications": "certifications", "certificates": "certifications"}
YEAR_RANGE_RE = re.compile(r"\b((?:19|20)\d{2})\s*(?:[-–—]|to)\s*((?:19|20)\d{2}|present|current)\b", re.IGNORECASE)
ROLE_RE = re.compile(r"\b(intern|ambassador|engineer|developer|lead|manager|researcher|president|coordinator)\b", re.IGNORECASE)


class ResumeParser:
    def parse(self, text: str) -> ParsedResume:
        lines = [self._clean_line(line) for line in text.splitlines() if self._clean_line(line)]
        sections = self._sections(lines)
        return ParsedResume(full_name=lines[0] if lines and len(lines[0]) < 80 and "@" not in lines[0] else None, email=self._find(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])", text), phone=self._indian_phone(text), linkedin_url=self._profile_url(r"linkedin\.com/(?:in|pub)/[^\s|,;)]+", text), github_url=self._profile_url(r"github\.com/[^\s|,;)]+", text), skills=self._skills(text), education=self._education(sections.get("education", [])), experience=self._experience(sections.get("experience", [])), projects=self._projects(sections.get("projects", [])), certifications=sections.get("certifications", []), raw_text=text)

    @staticmethod
    def _clean_line(line: str) -> str:
        return line.strip()

    @staticmethod
    def _is_bullet(line: str) -> bool:
        return bool(re.match(r"^[•●▪◦\-*]\s*", line))

    @classmethod
    def _content(cls, line: str) -> str:
        return re.sub(r"^[\s•●▪◦\-*]+", "", line).strip()

    @staticmethod
    def _find(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0).rstrip(".,;") if match else None

    @staticmethod
    def _profile_url(pattern: str, text: str) -> str | None:
        match = re.search(rf"(?:https?://)?(?:www\.)?{pattern}", text, re.IGNORECASE)
        return f"https://{match.group(0).removeprefix('http://').removeprefix('https://')}" if match else None

    @staticmethod
    def _indian_phone(text: str) -> str | None:
        match = re.search(r"(?<!\d)(?:\+91[\s.-]?|0091[\s.-]?|0)?[6-9]\d{4}[\s.-]?\d{5}(?!\d)", text)
        if not match: return None
        digits = re.sub(r"\D", "", match.group(0))
        return f"+91 {digits[-10:-5]} {digits[-5:]}"

    @staticmethod
    def _sections(lines: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}; current = ""
        for line in lines:
            heading = SECTION_NAMES.get(
    re.sub(r"[:|]+$", "", ResumeParser._content(line).strip().lower())
)
            if heading:
                current = heading; result.setdefault(current, []); continue
            if current: result[current].append(line)
        return result

    @staticmethod
    def _skills(text: str) -> list[str]:
        return list(dict.fromkeys(normalized for alias, normalized in SKILL_ALIASES.items() if re.search(rf"(?<![\w.]){re.escape(alias)}(?![\w.])", text, re.IGNORECASE)))

    
    @staticmethod
    def _dates(text: str) -> tuple[str | None, str | None]:
        year_range = re.search(
            r"(?<!\d)((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2}|present|current)\b",
            text,
            re.IGNORECASE
        )

        if year_range:
            return year_range.group(1), year_range.group(2)

        years = re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", text)

        if years:
            return years[0], years[-1]

        return None, None


    def _education(self, lines: list[str]) -> list[EducationEntry]:
        if not lines: return []
        joined = " ".join(lines); start, end = self._dates(joined)
        institution = re.split(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*(?:19|20)\d{2}\s*(?:[-–—]|to)", self._content(lines[0]), maxsplit=1, flags=re.IGNORECASE)[0].strip(" ,|- ")
        degree_line = next((line for line in lines if re.search(r"b\.?tech|bachelor|master|b\.?e\.?|m\.?tech", line, re.IGNORECASE)), "")
        degree = re.split(r"CGPA\b.*", degree_line, flags=re.IGNORECASE)[0].strip() or None
        cgpa = self._find(r"CGPA\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?\s*/\s*[0-9]+)", joined)
        if cgpa: cgpa = re.sub(r"^CGPA\s*[:：]?\s*", "", cgpa, flags=re.IGNORECASE)
        return [EducationEntry(institution=institution or None, degree=degree, start_date=start, end_date=end, graduation_year=end if end and end.isdigit() else None, cgpa=cgpa)]

    
    def _experience(self, lines: list[str]) -> list[ExperienceEntry]:
        records: list[list[str]] = []

        for line in lines:
            content = self._content(line)

            is_role = bool(ROLE_RE.search(content))
            is_bullet = self._is_bullet(line)

            if is_role and not is_bullet:
                records.append([line])
            elif records:
                records[-1].append(line)

        return [
            self._experience_record(record)
            for record in records
            if record
        ]


    
    def _experience_record(self, lines: list[str]) -> ExperienceEntry:
        first = self._content(lines[0])

        start, end = self._dates(first)

        role = first
        company = None

        ambassador = re.match(
            r"^(?P<company>.+?)\s+(?P<role>Student Ambassador)\b",
            first,
            re.IGNORECASE
        )

        if ambassador:
            company = ambassador.group("company").strip()
            role = ambassador.group("role").strip()

        elif re.search(r"\s+[–—-]\s+", first):
            parts = re.split(r"\s+[–—-]\s+", first, maxsplit=1)
            role = parts[0].strip()
            company = parts[1].strip()

        if company:
            company = re.sub(
                r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?"
                r"\s*(?:19|20)\d{2}(?:\s*[-–—]\s*"
                r"(?:19|20)\d{2})?\s*$",
                "",
                company,
                flags=re.IGNORECASE
            ).strip(" ,|-") or None

        description = " ".join(
            self._content(line)
            for line in lines[1:]
        ).strip() or None

        return ExperienceEntry(
            role=role,
            company=company,
            start_date=start,
            end_date=end,
            description=description
        )

    def _projects(self, lines: list[str]) -> list[ProjectEntry]:
        records: list[list[str]] = []
        for index, line in enumerate(lines):
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            starts_project = not self._is_bullet(line) and next_line.lower().startswith("technologies")
            if not records or starts_project:
                records.append([line])
            else:
                records[-1].append(line)
        return [self._project_record(record) for record in records if record]

    def _project_record(self, lines: list[str]) -> ProjectEntry:
        joined = " ".join(self._content(line) for line in lines); start, end = self._dates(joined)
        tech_line = next((self._content(line) for line in lines if self._content(line).lower().startswith("technologies")), "")
        description = " ".join(self._content(line) for line in lines[1:] if not self._content(line).lower().startswith("technologies")) or None
        return ProjectEntry(name=self._content(lines[0]), start_date=start, end_date=end, description=description, technologies=self._skills(tech_line or joined))
