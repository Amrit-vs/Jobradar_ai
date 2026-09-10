from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.mock_data import mock_jobs


class AmazonAdapter(JobSourceAdapter):
    slug = "amazon"
    careers_url = "https://www.amazon.jobs/"
    def get_company(self) -> str: return "Amazon"
    def fetch_jobs(self) -> list[NormalizedJob]: return mock_jobs(self.get_company(), self.slug, [("Backend Engineer", "Chennai, India", "0–2 years", "Java, AWS, DynamoDB"), ("Software Development Engineer", "Bengaluru, India", "2–5 years", "Java, microservices, AWS"), ("Machine Learning Engineer", "Seattle, United States", "2–5 years", "Python, PyTorch, SageMaker"), ("Data Scientist", "Toronto, Canada", "2–5 years", "SQL, Python, analytics"), ("Software Development Intern", "Pune, India", "Internship", "Java, algorithms")], "AMZN")

