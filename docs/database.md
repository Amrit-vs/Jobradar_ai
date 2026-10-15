# Database

PostgreSQL is the default datastore. The initial migration creates:

- `companies`: monitored-company configuration.
- `jobs`: normalized job records, unique by company and external job ID.
- `users` and `user_profiles`: future-ready candidate data.
- `resumes`: resume metadata and extracted text (files should remain private storage concerns).
- `collection_runs`: per-company mock collection outcome, counters, timestamps, and safe error summaries.

Run migrations with `alembic upgrade head` from `backend/`, or through the Docker command in the README. Phase 2 creates job and collection-run records only when `POST /api/admin/collect` is called.

Phase 3 extends `resumes` with file size, parsing status/error, parsed JSON data, and an active-resume flag. File bytes are processed transiently and are not stored in PostgreSQL.

Phase 3.5 declares the existing non-unique `ix_resumes_user_active` index in model
metadata to match migration `20260925_0003`. No new migration or data rewrite is
needed. PostgreSQL API activations serialize on the owning user row; this index
supports lookup but does not itself enforce uniqueness. Tests use the separate
memory-backed stack in `docker-compose.test.yml`, never the development volume.
