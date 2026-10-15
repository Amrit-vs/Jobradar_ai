# Roadmap

1. **Foundation — implemented:** FastAPI/React structure, SQLAlchemy models,
   Alembic migrations, PostgreSQL, and local Docker Compose development stack.
2. **Offline ingestion — implemented:** five mock adapters, 25 normalized jobs,
   deduplication, freshness, collection history, jobs/details, company status.
3. **Resume workflow — implemented:** PDF/DOCX upload, deterministic parsing,
   profile review/edit, active selection, and deletion. Parser heuristics are
   limited; OCR and a separate candidate-preferences workflow are absent.
3.5. **Stabilization:** preserve existing schema/indexes, enforce per-source
   transaction boundaries and disabled-company behavior, bound application
   upload reads, serialize active-resume requests, cover resume extraction/API
   workflows, lock baseline dependencies, and validate disposable PostgreSQL.
4. **Next proposed phase (not implemented):** configurable source-independent
   TF-IDF matching, ranking, explanations, and a functional minimum-score filter.
5. **Discovery workflow:** dashboard metrics, company management controls,
   candidate preferences, pagination, and expanded filtering.
6. **Permitted live sources:** documented adapters respecting source policies,
   rate limits, and access restrictions. Current adapters remain offline mocks.
7. **Notifications and scheduling.**
8. **Authentication and production operations:** production serving, monitoring,
   backups, and deployment hardening.

No phase implements automatic applications. Preferences, Alerts, and Settings
remain placeholders; Dashboard currently reuses the jobs page.
