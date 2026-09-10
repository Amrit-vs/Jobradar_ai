from app.schemas.jobs import NormalizedJob
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.mock_data import mock_jobs


class NvidiaAdapter(JobSourceAdapter):
    slug = "nvidia"
    careers_url = "https://www.nvidia.com/en-us/about-nvidia/careers/"
    def get_company(self) -> str: return "NVIDIA"
    def fetch_jobs(self) -> list[NormalizedJob]: return mock_jobs(self.get_company(), self.slug, [("AI Engineer", "Bengaluru, India", "0–2 years", "Python, CUDA, deep learning"), ("Computer Vision Engineer", "Pune, India", "2–5 years", "C++, OpenCV, PyTorch"), ("Senior Software Engineer", "Santa Clara, United States", "5+ years", "C++, GPU systems, Linux"), ("Machine Learning Intern", "Tel Aviv, Israel", "Internship", "Python, TensorFlow"), ("New Grad Software Engineer", "Taipei, Taiwan", "New Grad", "C++, data structures")], "NVDA")

