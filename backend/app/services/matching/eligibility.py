"""Conservative eligibility checks for explicitly labeled hard requirements."""
import re

from app.schemas.matching import EligibilityCheck, EligibilityResult, EligibilityStatus
from app.schemas.resume import EducationEntry, ParsedResume

LABELS = {
    "graduation_year": r"(?:required graduation years?|graduation years? required)",
    "degree": r"(?:required degree|degree required)",
    "experience": r"minimum (?:years of )?experience",
    "academic_percentage": r"minimum academic percentage",
}
DEGREES = {
    "btech": "btech", "b tech": "btech", "bachelor of technology": "btech",
    "be": "be", "b e": "be", "bachelor of engineering": "be",
    "bsc": "bsc", "b sc": "bsc", "bachelor of science": "bsc",
    "bca": "bca", "bachelor of computer applications": "bca",
    "mtech": "mtech", "m tech": "mtech", "master of technology": "mtech",
    "me": "me", "m e": "me", "master of engineering": "me",
    "msc": "msc", "m sc": "msc", "master of science": "msc",
    "mca": "mca", "master of computer applications": "mca",
    "bachelor": "bachelor", "bachelors": "bachelor", "bachelor s": "bachelor",
    "master": "master", "masters": "master", "master s": "master",
}
BACHELORS = {"btech", "be", "bsc", "bca", "bachelor"}
MASTERS = {"mtech", "me", "msc", "mca", "master"}


def requirements(description: str) -> dict[str, str]:
    result: dict[str, str] = {}
    clauses = re.split(r"[\n;]+|(?<=[.!?])\s+(?=(?:Required|Minimum|Degree|Graduation)\b)", description, flags=re.IGNORECASE)
    for criterion, label in LABELS.items():
        values = []
        for clause in clauses:
            match = re.fullmatch(rf"\s*(?:[-•]\s*)?{label}\s*:\s*(.+?)\s*[.]?\s*", clause, re.IGNORECASE)
            if match:
                values.append(match.group(1).strip().rstrip("."))
        if values:
            result[criterion] = " | ".join(dict.fromkeys(values))
    return result


def degree_name(value: str, *, candidate: bool = False) -> str | None:
    text = " ".join(re.sub(r"[^a-z ]", " ", value.casefold()).split())
    text = re.sub(r"\s+degree$", "", text)
    if text in DEGREES:
        return DEGREES[text]
    if candidate:
        # A longer candidate degree can satisfy a generic degree-type requirement.
        for name in sorted(DEGREES, key=lambda item: (-len(item), item)):
            if text.startswith(name + " "):
                return DEGREES[name]
    return None


def combine(checks: list[EligibilityCheck]) -> EligibilityStatus:
    required = [check for check in checks if check.requirement is not None]
    if any(check.status == "ineligible" for check in required):
        return "ineligible"
    if not required or any(check.status == "unknown" for check in required):
        return "unknown"
    return "eligible"


def evaluate_education(entry: EducationEntry | None, required: dict[str, str]) -> list[EligibilityCheck]:
    checks = []
    for criterion in ("graduation_year", "degree", "academic_percentage"):
        value = required.get(criterion)
        check = EligibilityCheck(criterion=criterion, requirement=value, reason="No supported explicit hard requirement is stated in the job description.")
        if value is None:
            checks.append(check)
            continue
        actual = None if entry is None else getattr(entry, "percentage" if criterion == "academic_percentage" else criterion)
        check.candidate_value = str(actual) if actual is not None else None
        check.reason = "The saved profile does not supply this qualification; eligibility is unknown."
        if criterion == "graduation_year":
            years = re.fullmatch(r"((?:19|20)\d{2})(?:\s*[-–]\s*((?:19|20)\d{2}))?", value)
            allowed = None
            if years:
                first, last = int(years[1]), int(years[2] or years[1])
                if first <= last:
                    allowed = set(range(first, last + 1))
            elif re.fullmatch(r"(?:19|20)\d{2}(?:\s*(?:,|or)\s*(?:19|20)\d{2})+", value, re.IGNORECASE):
                allowed = {int(year) for year in re.findall(r"(?:19|20)\d{2}", value)}
            if allowed is None:
                check.reason = "The explicit graduation requirement has unsupported or conflicting wording."
            elif actual is not None and re.fullmatch(r"(?:19|20)\d{2}", str(actual)):
                check.status = "eligible" if int(actual) in allowed else "ineligible"
                check.reason = f"Saved graduation year {actual} {'meets' if check.status == 'eligible' else 'does not meet'} the explicit year requirement."
        elif criterion == "degree":
            options = [degree_name(option.strip()) for option in re.split(r"\bor\b|/", value, flags=re.IGNORECASE)]
            candidate = degree_name(str(actual), candidate=True) if actual else None
            if not all(options):
                check.reason = "The degree requirement includes unsupported qualifications or equivalencies; manual review is needed."
            elif candidate:
                accepted = candidate in options or ("bachelor" in options and candidate in BACHELORS) or ("master" in options and candidate in MASTERS)
                if not accepted and ((candidate == "bachelor" and any(option in BACHELORS for option in options)) or (candidate == "master" and any(option in MASTERS for option in options))):
                    check.reason = "The saved degree level is too broad to establish the specific required degree type."
                else:
                    check.status = "eligible" if accepted else "ineligible"
                    check.reason = f"Saved degree {actual} {'meets' if accepted else 'does not meet'} the explicit degree types. No degree equivalence is assumed."
        else:
            minimum = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", value)
            if minimum is None or not 0 <= float(minimum[1]) <= 100:
                check.reason = "The academic requirement must explicitly specify a percentage from 0 to 100."
            elif actual is not None:
                accepted = actual >= float(minimum[1])
                check.status = "eligible" if accepted else "ineligible"
                check.reason = f"Saved academic percentage {actual:g}% {'meets' if accepted else 'is below'} the explicit minimum. CGPA is never converted."
        checks.append(check)
    return checks


def evaluate_eligibility(profile: ParsedResume | None, description: str) -> EligibilityResult:
    required = requirements(description)
    # All education criteria must be satisfied by the SAME qualification, not
    # a graduation year from one degree and a percentage from another.
    alternatives = [evaluate_education(entry, required) for entry in (profile.education if profile and profile.education else [None])]
    priority = {"eligible": 2, "unknown": 1, "ineligible": 0}
    education = max(alternatives, key=lambda checks: (priority[combine(checks)], sum(check.status == "eligible" for check in checks)))
    experience = EligibilityCheck(criterion="experience", requirement=required.get("experience"), reason="No supported explicit minimum experience requirement is stated.")
    if experience.requirement is not None:
        actual = profile.years_of_experience if profile else None
        experience.candidate_value = str(actual) if actual is not None else None
        minimum = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", experience.requirement, re.IGNORECASE)
        if minimum is None:
            experience.reason = "The minimum experience wording is unsupported or ambiguous."
        elif actual is None:
            experience.reason = "Total years of experience is not explicitly saved; dates, titles, and internships are not converted into years."
        else:
            accepted = actual >= float(minimum[1])
            experience.status = "eligible" if accepted else "ineligible"
            experience.reason = f"Saved total experience {actual:g} years {'meets' if accepted else 'is below'} the explicit minimum."
    checks = [*education, experience]
    return EligibilityResult(status=combine(checks), checks=checks)
