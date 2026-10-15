# JobRadar AI

JobRadar AI is a multi-company job discovery foundation. Phase 2 adds an offline multi-company ingestion pipeline with 25 mock jobs. It does **not** collect live jobs, parse resumes, score matches, notify users, authenticate users, or apply for jobs.

## Quick start

1. Copy `.env.example` to `.env` and replace the example database password.
2. Start the stack: `docker compose up --build`.
3. Apply the schema: `docker compose exec backend alembic upgrade head`.
4. Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs`.
5. Use **Run Job Collection** in the UI, or call `POST /api/admin/collect`, to load mock jobs.
6. Open **Resume & Profile** to upload a PDF/DOCX resume for local, deterministic parsing.

## Local development

Backend (Python 3.12+):

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
pytest
```

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev
npm test
```

See [architecture documentation](docs/architecture.md) and [database documentation](docs/database.md).
