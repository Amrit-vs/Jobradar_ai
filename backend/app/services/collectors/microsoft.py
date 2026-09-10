from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.mock_data import mock_jobs


class MicrosoftAdapter(JobSourceAdapter):
    slug = "microsoft"
    careers_url = "https://careers.microsoft.com/"
    def get_company(self) -> str: return "Microsoft"
    def fetch_jobs(self) -> list[NormalizedJob]: return mock_jobs(self.get_company(), self.slug, [("AI Engineer", "Bengaluru, India", "0–2 years", "Python, Azure, machine learning"), ("Frontend Engineer", "Noida, India", "2–5 years", "TypeScript, React, accessibility"), ("Data Scientist", "Redmond, United States", "2–5 years", "Python, SQL, statistics"), ("Software Engineer, New Grad", "Vancouver, Canada", "New Grad", "C#, algorithms, Azure"), ("Software Engineering Intern", "Hyderabad, India", "Internship", "JavaScript, data structures")], "MSFT")

