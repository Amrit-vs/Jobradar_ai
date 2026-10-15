# Database

PostgreSQL is the default datastore. The initial migration creates:

- `companies`: monitored-company configuration.
- `jobs`: normalized job records, unique by company and external job ID.
- `users` and `user_profiles`: future-ready candidate data.
- `resumes`: resume metadata and extracted text (files should remain private storage concerns).
- `collection_runs`: per-company mock collection outcome, counters, timestamps, and safe error summaries.

Run migrations with `alembic upgrade head` from `backend/`, or through the Docker command in the README. Phase 2 creates job and collection-run records only when `POST /api/admin/collect` is called.

Phase 3 extends `resumes` with file size, parsing status/error, parsed JSON data, and an active-resume flag. File bytes are processed transiently and are not stored in PostgreSQL.
