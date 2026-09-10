from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.mock_data import mock_jobs


class GoogleAdapter(JobSourceAdapter):
    slug = "google"
    careers_url = "https://careers.google.com/"
    def get_company(self) -> str: return "Google"
    def fetch_jobs(self) -> list[NormalizedJob]: return mock_jobs(self.get_company(), self.slug, [("Software Engineer, New Grad", "Bengaluru, India", "New Grad", "Python, Java, distributed systems"), ("Machine Learning Engineer", "Hyderabad, India", "0–2 years", "Python, TensorFlow, SQL"), ("Backend Engineer", "Dublin, Ireland", "2–5 years", "Go, APIs, PostgreSQL"), ("Software Engineering Intern", "London, United Kingdom", "Internship", "C++, algorithms"), ("Senior Software Engineer", "Mountain View, United States", "5+ years", "Java, Kubernetes, cloud")], "GOOG")

