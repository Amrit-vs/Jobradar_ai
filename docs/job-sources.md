# Job sources

Phase 2 uses five offline mock adapters: Google, Microsoft, Amazon, NVIDIA, and Adobe. Each returns five `NormalizedJob` Pydantic objects (25 total) with `source="MOCK"`.

The ingestion service consumes only `JobSourceAdapter.fetch_jobs()`, not source-specific implementations. It first deduplicates by `(company_id, external_job_id)` and then falls back to company/title/location/URL. Existing records retain their ID and `first_seen_at`; changed records update in place and every rediscovery updates `last_seen_at`.

To add a future permitted company source:

1. Create an adapter implementing `JobSourceAdapter`.
2. Return validated `NormalizedJob` objects.
3. Register the adapter in `CompanyAdapterRegistry`.
4. Add mocked adapter and ingestion tests.

No source may invent endpoints, bypass protections, or apply for a user.
