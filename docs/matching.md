# Explainable matching (Phase 4)

Matching is deterministic and local: no external LLM, paid API, model download,
or internet access. The implementation uses Python's standard library, existing
Pydantic schemas, and existing database sessions. No migration or dependency
upgrade is required.

## Inputs and review

The active resume must belong to the configured development user, have completed
parsing, and contain valid saved `ParsedResume` JSON. Activation is the existing
review/selection action; a separate reviewed flag is not stored. The UI asks the
user to review and save corrections before activation. Zero active resumes,
invalid/failed active profiles, and multiple active resumes have explicit states.
The service does not create users, silently select an alternative resume, or
rewrite existing records.

Candidate text uses saved skills, education degree/field, experience roles and
descriptions, projects and technologies, and certifications. It excludes raw
extracted text, name, contact details, institution names, employer names, dates,
and personal location. Changes to saved data take effect on the next request;
there is no persisted-score cache. Inactive uploads do not replace the active
resume. A contact-only/empty profile has no score, rather than an invented zero.

## Skills and text similarity

The skill vocabulary reuses the parser aliases and extends them with additional
job technologies. Aliases such as Python3/Python, ReactJS/React, Postgres/PostgreSQL,
and NodeJS/Node.js normalize to one name. Longest-first bounded matching keeps
C, C++, C#, Java, and JavaScript separate. Unknown technologies can contribute
through text similarity but are not invented as recognized skills. This finite
vocabulary is heuristic: a mention does not establish proficiency, mandatory
status, or context such as negation. Preferred/optional mentions can appear in
matched/missing skills; they never become hard eligibility requirements.

Job skills are recognized from the job title and description, independent of
candidate skills. Skill coverage is:

```
skill_overlap = count(candidate_skills intersect job_skills) / count(job_skills)
```

Job text is title plus description. Both documents use the same alias-aware,
case-normalized tokenizer and a fixed small stop-word set. Term frequency is
raw occurrence count. Smoothed inverse document frequency is fitted to exactly
the candidate/job pair (N=2):

```
idf(term) = ln((1 + N) / (1 + document_frequency(term))) + 1
vector(term, document) = term_frequency(term, document) * idf(term)
text_similarity = dot(candidate_vector, job_vector) / (norm(candidate) * norm(job))
score = 100 * (skill_weight * skill_overlap + text_weight * text_similarity)
```

Weights default to 0.6 skill coverage / 0.4 text similarity. Configure
`MATCHING_SKILL_WEIGHT` and `MATCHING_TEXT_WEIGHT` in `.env` or the environment;
Compose forwards both. Values must be finite and in [0,1], with positive total.
Available weights are normalized to sum to one. A component with insufficient
job data is null and its weight is redistributed across available enabled
components. Missing candidate skills against recognized job skills score zero;
no recognized job skills makes that component unavailable. If no enabled
component is available, the overall score is null. Component and total scores
are rounded to two decimals; the total uses unrounded components.

Pairwise fitting deliberately keeps scores identical between list/detail views
and stable as other jobs are added or filters change. This differs from fitting
one changing corpus of all jobs. Scores describe lexical relevance, not a hiring
probability, semantic understanding, verified proficiency, or eligibility.

## Conservative eligibility

Eligibility is separate from scoring and never changes the score or hides jobs.
Four checks always return a status and reason: graduation year, degree, total
experience, academic percentage. Supported hard requirements must be explicitly
labeled, on separate lines, separated by semicolons, or in separate sentences:

```
Required graduation year: 2026
Required graduation years: 2025-2027
Required graduation years: 2025 or 2026
Required degree: B.Tech or B.E.
Required degree: Bachelor's degree
Minimum experience: 2 years
Minimum academic percentage: 60%
```

`Graduation year required:` and `Degree required:` labels are also supported.
Degree types include B.Tech, B.E., B.Sc., BCA, M.Tech, M.E., M.Sc., MCA, and their
full names. Generic bachelor/master requirements accept explicitly saved
recognized degree types at that level. Specific degree types are not assumed
equivalent. Field-specific degree requirements and 'or equivalent' are unknown.
Multiple or conflicting requirement values, unsupported phrasing, preferred
qualifications, New Grad/Senior labels, and experience-level display strings are
not inferred into hard rules.

The candidate year and degree come from saved education entries. All education
requirements must be met by the same entry, never assembled across degrees.
Optional saved `percentage` is compared directly; CGPA is not converted. Optional
saved `years_of_experience` is compared directly; dates, overlapping roles,
internships, and current dates are not converted into years. Both optional
fields default to null in old resumes and can be reviewed/entered in the editor.

- **Ineligible:** an explicit recognized requirement is demonstrably unmet, and
  no alternative qualification satisfies or leaves that education decision open.
- **Unknown:** no supported explicit criteria exist, required candidate data is
  absent, or a recognized requirement cannot be interpreted safely.
- **Eligible:** all identified supported explicit criteria are met. Unspecified
  criteria remain unknown per-check; the overall decision covers only identified
  criteria and is not a claim that every possible job condition was evaluated.

Every check includes the job requirement and saved candidate value when
available, plus a human-readable reason. Users must review the full posting for
conditions outside this limited grammar. Mock postings currently specify skills
but no supported hard academic/experience criteria, so eligibility is unknown.

## API and UI

`GET /api/jobs` still returns an array and keeps posted-date order by default.
All existing filters remain available. Each list/detail item adds:

- `match_score`: number 0–100, or null when unavailable.
- `matching`: status, selected resume ID, matched/missing skill lists,
  `components`, effective `weights`, eligibility checks, explanation, method.

`GET /api/jobs?sort_by=match_score&min_match_score=50` sorts descending by score
and includes only scores >=50. `sort_by=posted_at` is the default. Ties retain
posted-date/ID ordering. Null scores are last for best-match sorting and excluded
by any explicit minimum, including zero. Out-of-range minima and unsupported
sort values return 422. Applying company/location/title filters does not alter
an individual score. Eligibility remains independent of score filtering.

`GET /api/matching/context` explains readiness even when no jobs exist. Matching
GETs do not mutate users or resumes. The UI displays scores, skill differences,
component weights and eligibility evidence; score controls are unavailable until
a usable active profile exists. Existing browsing remains usable. Profile save,
activation, and deletion invalidate matching/jobs caches.

## Verification and current limits

Tests cover exact TF-IDF arithmetic, normalization, missing data, weights,
repeatability, ranking/filtering, list/detail consistency, conservative eligibility,
profile edit/activation/deletion, and frontend controls/empty states. Existing
resume, ingestion, and PostgreSQL activation tests remain part of validation.
Use the disposable database procedure in the README for migration/Alembic checks.

Matching computes per job on each request; no pagination or persistent index is
added. This is appropriate for the current 25-job offline dataset, and should be
profiled before scaling. English/technical vocabulary, limited requirement
formats, parser accuracy, and explicitly reviewed profile completeness constrain
results. Live sources, scheduling, authentication, and alerts remain out of scope.
