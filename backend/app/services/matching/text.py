import math
import re
from collections import Counter

from app.schemas.resume import ParsedResume
from app.services.resume.parser import SKILL_ALIASES

# Extend the existing parser vocabulary without changing resume parsing behavior.
ALIASES = {**SKILL_ALIASES, "c#": "C#", "csharp": "C#", "golang": "Go", "go": "Go", "rust": "Rust", "cuda": "CUDA", "linux": "Linux", "redis": "Redis", "dynamodb": "DynamoDB", "sagemaker": "SageMaker", "css": "CSS", "html": "HTML", "generative ai": "Generative AI", "distributed systems": "Distributed Systems", "microservices": "Microservices", "algorithms": "Algorithms", "data structures": "Data Structures"}
SKILL_RE = re.compile(r"(?<![\w+#])(?:" + "|".join(re.escape(alias) for alias in sorted(ALIASES, key=lambda value: (-len(value), value))) + r")(?![\w+#])", re.IGNORECASE)
STOP_WORDS = frozenset("a an and are as at be by for from in is it of on or our that the their this to we with you your required requirements preferred minimum must have experience skills".split())


def normalize_skill(value: str) -> str:
    cleaned = " ".join(value.strip().split()).casefold()
    return ALIASES.get(cleaned, cleaned)


def extract_skills(text: str) -> set[str]:
    return {ALIASES[match.group().casefold()] for match in SKILL_RE.finditer(text)}


def resume_text(profile: ParsedResume) -> str:
    """Only saved professional fields: never stale raw text or personal identifiers."""
    values = [*profile.skills, *profile.certifications]
    for entry in profile.education:
        values.extend([entry.degree or "", entry.field_of_study or ""])
    for entry in profile.experience:
        values.extend([entry.role or "", entry.description or ""])
    for entry in profile.projects:
        values.extend([entry.name or "", entry.description or "", *entry.technologies])
    return "\n".join(value.strip() for value in values if value.strip())


def tokens(text: str) -> list[str]:
    text = SKILL_RE.sub(lambda match: ALIASES[match.group().casefold()].casefold().replace(" ", "_"), text)
    return [token for token in re.findall(r"[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*[+#]*", text.casefold()) if token not in STOP_WORDS]


def cosine_tfidf(left: str, right: str) -> float | None:
    """Smoothed IDF over exactly two documents, stable across filtering and ingestion."""
    counts = [Counter(tokens(left)), Counter(tokens(right))]
    if not all(counts):
        return None
    vocabulary = sorted(set(counts[0]) | set(counts[1]))
    idf = {term: math.log(3 / (1 + sum(term in count for count in counts))) + 1 for term in vocabulary}
    vectors = [{term: count[term] * idf[term] for term in vocabulary} for count in counts]
    dot = sum(vectors[0][term] * vectors[1][term] for term in vocabulary)
    norms = [math.sqrt(sum(value * value for value in vector.values())) for vector in vectors]
    return min(1.0, max(0.0, dot / (norms[0] * norms[1])))
