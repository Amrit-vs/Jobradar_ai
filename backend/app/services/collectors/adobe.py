from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.mock_data import mock_jobs


class AdobeAdapter(JobSourceAdapter):
    slug = "adobe"
    careers_url = "https://careers.adobe.com/"
    def get_company(self) -> str: return "Adobe"
    def fetch_jobs(self) -> list[NormalizedJob]: return mock_jobs(self.get_company(), self.slug, [("Frontend Engineer", "Noida, India", "0–2 years", "React, TypeScript, CSS"), ("Data Scientist", "Bengaluru, India", "2–5 years", "Python, SQL, experimentation"), ("AI Engineer", "San Jose, United States", "2–5 years", "Python, generative AI, cloud"), ("Software Engineer, New Grad", "Bucharest, Romania", "New Grad", "Java, algorithms"), ("Software Engineering Intern", "Bengaluru, India", "Internship", "JavaScript, React")], "ADBE")

