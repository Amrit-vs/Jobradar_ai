# JobRadar AI

JobRadar AI is a local job discovery application built with FastAPI, SQLAlchemy,
PostgreSQL, Alembic, React, TypeScript, Tailwind CSS, and Docker Compose.

## Implemented features

- Five offline adapters (Google, Microsoft, Amazon, NVIDIA, Adobe), producing 25
  explicitly labeled mock jobs. No external job site is contacted.
- Source-independent normalization, deduplication, updates, freshness labels,
  per-company collection history, and isolation of failed collection batches.
  Companies marked disabled in the database are skipped; company editing UI is
  not implemented.
- API-backed jobs, job details, basic filters, and company status/counts.
- PDF/DOCX resume upload, local deterministic extraction/parsing, saved profile
  edits, active-resume selection, and deletion (including failed uploads).
  Scanned PDFs require OCR, which is not implemented.
- Phase 3.5 stabilization: schema metadata consistency, ingestion regression
  coverage, bounded application upload reads, PostgreSQL activation locking,
  resume lifecycle tests, and dependency locks.

Matching, ranking, live sources, scheduled collection, notifications, and
authentication are not implemented. Dashboard currently shows the jobs list;
Preferences, Alerts, and Settings are placeholders. All resume requests use one
configured development user. This stack is intended for local development.

## Windows quick start (Docker Desktop)

Use Docker Desktop with Linux containers and Docker Compose. This avoids needing
host Python, npm, or PostgreSQL. Run commands from the repository root.

1. If `.env` does not already exist, copy `.env.example` to `.env`. Preserve an
   existing file. Choose a database password and update both `POSTGRES_PASSWORD`
   and the host `DATABASE_URL` consistently; URL-encode special characters in URLs.
2. Run `docker compose up --build`. Backend startup applies migrations
   automatically; an additional migration command is unnecessary.
3. Open `http://localhost:5173`; API documentation is at
   `http://localhost:8000/docs`.
4. Use **Run Job Collection** to populate mock jobs, then **Resume & Profile** to
   upload and review a resume.

Compose uses its `db` hostname internally; the example `DATABASE_URL` uses
`localhost` for a backend running on Windows. Compose forwards environment,
CORS, resume-size, and development-user settings from `.env`. Resume size is
controlled by `MAX_RESUME_SIZE_MB` (default 10). `MAX_UPLOAD_SIZE_MB` is reserved
for future generic uploads and does not override the resume limit.

The default frontend API URL is `http://localhost:8000/api`. For a host-based
frontend, set `VITE_API_URL` in `frontend/.env.local` if needed. The Compose
frontend currently uses that default local URL.

The regular Compose database uses a persistent volume. Do not use
`docker compose down -v` or migration downgrades against a database containing
user data. Existing database credentials must match the initialized volume;
editing `.env` does not change its password.

## Host-based development (PowerShell)

Use Python 3.12 and Node 20 with npm (the verified Docker baseline uses Node 20).
No global Python packages are required. Keep a configured `.env` at the
repository root; run backend commands from that root so settings load it.
Point `DATABASE_URL` to a prepared development PostgreSQL database on `localhost`.
Applying migrations changes its schema, so use a dedicated development database.

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock
& backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade head
& backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload
```

In another PowerShell window:

```powershell
Push-Location frontend
npm ci
npm run dev
Pop-Location
```

`requirements.txt` defines allowed direct dependencies; `requirements.lock`
pins the complete verified Python 3.12 baseline, with platform markers for
Windows-only colorama and non-Windows uvloop. Native Windows installation has
not been verified; Docker Linux is the verified path. `package-lock.json` comes
from the verified frontend image, and Docker uses `npm ci`. No dependency
upgrades are part of Phase 3.5. Deliberate dependency changes should update the
locks and rerun all checks. Base image tags are not digest-pinned.

## Tests and disposable PostgreSQL validation

For already installed host dependencies, run backend tests from the root with
`backend/.venv/Scripts/python.exe -m pytest -c backend/pytest.ini backend/tests`.
From `frontend`, run `npm test` and `npm run build`. Unit/API tests use in-memory
SQLite. The PostgreSQL concurrency test is skipped unless explicitly configured.

For isolated Windows validation, use the separate test Compose file. It defines
no persistent volumes or published ports. The PostgreSQL database lives in
memory, and a unique project name keeps this separate from the development stack.

```powershell
$verifyProject = "jobradar-verify-" + [Guid]::NewGuid().ToString("N")
$env:JOBRADAR_TEST_PASSWORD = [Guid]::NewGuid().ToString("N")
try {
    docker compose -p $verifyProject -f docker-compose.test.yml build
    if ($LASTEXITCODE -ne 0) { throw "Test image build failed" }
    docker compose -p $verifyProject -f docker-compose.test.yml run --rm backend
    if ($LASTEXITCODE -ne 0) { throw "Backend or migration checks failed" }
    docker compose -p $verifyProject -f docker-compose.test.yml run --rm --no-deps frontend
    if ($LASTEXITCODE -ne 0) { throw "Frontend checks failed" }
} finally {
    docker compose -p $verifyProject -f docker-compose.test.yml down
    Remove-Item Env:JOBRADAR_TEST_PASSWORD
}
```

Backend validation applies migrations, runs `alembic check`, and runs all tests,
including concurrent activation against PostgreSQL. Never point
`TEST_POSTGRES_URL` at an existing user database; it additionally requires
`TEST_DATABASE_DISPOSABLE=1`. Tests do not depend on external job sites.

See [architecture](docs/architecture.md), [database](docs/database.md),
[resume pipeline](docs/resume-pipeline.md), and [roadmap](docs/roadmap.md).
