from app.services.resume.parser import ResumeParser


def test_parser_extracts_contact_skills_and_sections() -> None:
    parsed = ResumeParser().parse("""Ada Developer
ada@example.test | +91 98765 43210
https://linkedin.com/in/ada https://github.com/ada
Skills
Python3, ReactJS, Postgres, Docker
Education
Example Institute B.Tech Computer Science 2026
Experience
Software Engineering Intern
Built APIs with FastAPI.
Projects
Job Radar
Resume discovery project.
Certifications
Cloud Fundamentals
""")
    assert parsed.full_name == "Ada Developer"
    assert parsed.email == "ada@example.test"
    assert parsed.github_url == "https://github.com/ada"
    assert {"Python", "React", "PostgreSQL", "Docker"}.issubset(parsed.skills)
    assert parsed.education[0].institution.startswith("Example Institute")
    assert parsed.projects[0].name == "Job Radar"


def test_parser_allows_missing_sections() -> None:
    parsed = ResumeParser().parse("Candidate\ncandidate@example.test")
    assert parsed.email == "candidate@example.test"
    assert parsed.skills == []
    assert parsed.education == []


def test_parser_handles_indian_contact_details_and_graduation_year() -> None:
    parsed = ResumeParser().parse("""Sample Candidate
sample.candidate@example.test | +91-98765 43210 | linkedin.com/in/sample-candidate | github.com/sample-candidate
EDUCATION:
Example University | B.Tech Computer Science | 2023 – 2027
INTERNSHIPS
Backend Engineering Intern
Example Labs
• Built FastAPI services with PostgreSQL.
PROJECTS
Job Board | Python, React, Docker | 2024 - 2025
• Full stack job discovery application.
CERTIFICATES
Cloud Foundations
""")
    assert parsed.email == "sample.candidate@example.test"
    assert parsed.phone == "+91 98765 43210"
    assert parsed.linkedin_url == "https://linkedin.com/in/sample-candidate"
    assert parsed.github_url == "https://github.com/sample-candidate"
    assert parsed.education[0].graduation_year == "2027"
    assert parsed.experience[0].role == "Backend Engineering Intern"
    assert parsed.projects[0].name.startswith("Job Board")
    assert {"Python", "React", "Docker"}.issubset(parsed.projects[0].technologies)


def test_parser_handles_technical_headings_merged_dates_and_multiple_records() -> None:
    parsed = ResumeParser().parse("""Synthetic Candidate
Education
Example University, Sample CitySep 2023 – 2027
Bachelor of Technology in Computer Science and EngineeringCGPA: 8.7/10
Technical Skills
Python, React, Docker
Technical Projects
Project One – Platform (In Development)
Technologies: Python, React, Docker
• First capability wraps onto
the following extracted line.
Project Two
Technologies: Python, FastAPI
• Second project description.
Project Three
Technologies: SQL, PostgreSQL
• Third project description.
Experience and Leadership
Machine Learning Summer Intern – Example Centre, Sample City, 2025
• Built a prototype.
Student Ambassador, Apr 2026 – Sep 2026
• Led student outreach.
Certifications
Synthetic Cloud Credential
""")
    assert parsed.education[0].institution == "Example University, Sample City"
    assert parsed.education[0].degree == "Bachelor of Technology in Computer Science and Engineering"
    assert parsed.education[0].graduation_year == "2027"
    assert parsed.education[0].cgpa == "8.7/10"
    assert len(parsed.projects) == 3
    assert parsed.projects[0].name.startswith("Project One")
    assert "following extracted line" in (parsed.projects[0].description or "")
    assert len(parsed.experience) == 2
    assert parsed.experience[0].role == "Machine Learning Summer Intern"
    assert parsed.experience[1].role == "Student Ambassador, Apr 2026"
    assert parsed.certifications == ["Synthetic Cloud Credential"]


def test_project_bullets_do_not_create_false_project_records() -> None:
    parsed = ResumeParser().parse("""Technical Projects
Career Discovery Platform – Resume Management (In Development)
Technologies: Python, FastAPI, PostgreSQL
• Implemented backend endpoints for resume upload.
• Evaluated models using precision and recall.
  Results are displayed in a dashboard.
Conversational Assistant Application
Technologies: Python, React
• Built a conversational interface.
Placement Readiness Prediction System
Technologies: Python, SQL
• Trained a classification model.
Experience and Leadership
AI Summer Intern – Example Centre, Sample City, 2025
• Built prototype features.
Example Student Ambassador, Apr 2026 – Sep 2026
• Coordinated student outreach.
""")
    assert len(parsed.projects) == 3
    assert [project.name for project in parsed.projects] == [
        "Career Discovery Platform – Resume Management (In Development)",
        "Conversational Assistant Application",
        "Placement Readiness Prediction System",
    ]
    assert "Implemented backend endpoints" in (parsed.projects[0].description or "")
    assert "Results are displayed" in (parsed.projects[0].description or "")
    assert parsed.experience[0].company == "Example Centre, Sample City"
    assert parsed.experience[0].start_date == "2025"
    assert parsed.experience[1].company == "Example"
    assert parsed.experience[1].role == "Student Ambassador"
    assert parsed.experience[1].start_date == "2026"
    assert parsed.experience[1].end_date == "2026"


def test_experience_keeps_adjacent_entries_and_strips_merged_year() -> None:
    parsed = ResumeParser().parse("""Experience and Leadership
AI and Machine Learning Summer Intern – Example Technology Centre, Sample City2025
• Built a proof of concept.
  Kept the wrapped detail with the internship.
Example Student Ambassador, Apr 2026 – Sep 2026
• Led student activities.
""")
    assert len(parsed.experience) == 2
    assert parsed.experience[0].role == "AI and Machine Learning Summer Intern"
    assert parsed.experience[0].company == "Example Technology Centre, Sample City"
    assert parsed.experience[0].start_date == "2025"
    assert "wrapped detail" in (parsed.experience[0].description or "")
    assert parsed.experience[1].company == "Example"
    assert parsed.experience[1].role == "Student Ambassador"
    assert parsed.experience[1].start_date == "2026"
    assert parsed.experience[1].end_date == "2026"
    assert "Led student activities" in (parsed.experience[1].description or "")
