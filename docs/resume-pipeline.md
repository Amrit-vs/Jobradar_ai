# Resume pipeline

```
Upload PDF/DOCX → validation → local text extraction → rule-based parsing
→ structured profile → user review/edit → Phase 4 matching
```

Phase 3 accepts PDF and DOCX files up to the configured `MAX_RESUME_SIZE_MB` (10 MB by default). `pypdf` extracts text-based PDFs and `python-docx` reads paragraphs and simple table text. Scanned PDFs return an explicit OCR-not-supported error.

Parsing is local and deterministic: section headings, regular expressions, and a configured skill alias dictionary extract only visible information. It does not use an LLM, embeddings, internet access, or OCR. Users can edit saved parsed data; refreshes do not trigger reparsing.

Phase 3 does not implement matching, notifications, live sources, or automatic applications.

Phase 4 consumes saved active profiles for deterministic matching. Activation is
the existing explicit review/selection action; no separate reviewed flag exists.
Save corrections before activation. Optional `years_of_experience` and each
education entry's `percentage` can be entered in the editor and saved in the
existing JSON. They default to unknown, including for previously saved resumes.
They are not estimated from dates or CGPA. Matching excludes `raw_text`, names,
contact details, and institution/company names so stale extracted text cannot
override saved corrections. See [matching](matching.md) for eligibility scope.

Phase 3.5 reads at most the configured size limit plus one byte into application
memory before rejecting an oversized upload. Multipart parsing may already spool
the request to temporary storage; this is not a transport-level body limit or a
limit on decompressed document content.

Activation requests lock the owning user row with PostgreSQL `FOR UPDATE` before
reading or changing active flags. This serializes concurrent API activations
without a new migration or changing existing records. SQLite unit tests do not
provide this locking guarantee; the opt-in PostgreSQL HTTP concurrency test does.
Direct SQL writers must follow the same locking protocol. Existing duplicate
active flags are not automatically rewritten; the next activation for that user
normalizes them. Failed extraction records remain visible and can be deleted.
