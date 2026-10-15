# Architecture

JobRadar AI is a monorepo with a React/Vite frontend and a FastAPI backend. PostgreSQL is the production database; SQLAlchemy models express persistence and Alembic owns schema migrations.

```
React + TypeScript → FastAPI REST API → SQLAlchemy → PostgreSQL
```

The backend is organized by responsibility: `api` exposes HTTP routes, `core` contains configuration, `db` owns sessions, `models` define persistence, `schemas` define API contracts, and `services` is reserved for domain behavior. Future collectors, matching engines, resume processors, ranking, and notifications belong under `services` behind interfaces, keeping them independent from routes and the database implementation.

Phase 2 adds an internal ingestion pipeline: `JobSourceAdapter → NormalizedJob → JobIngestionService → PostgreSQL → API → React`. The registry supplies adapters; the ingestion service contains no company-specific code. Every current adapter is an offline `MOCK` source, and no external job site is contacted.

Phase 3 adds a local resume pipeline: upload validation → PDF/DOCX extraction → deterministic parsing → validated JSON profile data → user review. It is isolated under `services/resume` so a later parser can be introduced without changing upload APIs.
