# Resume pipeline

```
Upload PDF/DOCX → validation → local text extraction → rule-based parsing
→ structured profile → user review/edit → Phase 4 matching
```

Phase 3 accepts PDF and DOCX files up to the configured `MAX_RESUME_SIZE_MB` (10 MB by default). `pypdf` extracts text-based PDFs and `python-docx` reads paragraphs and simple table text. Scanned PDFs return an explicit OCR-not-supported error.

Parsing is local and deterministic: section headings, regular expressions, and a configured skill alias dictionary extract only visible information. It does not use an LLM, embeddings, internet access, or OCR. Users can edit saved parsed data; refreshes do not trigger reparsing.

Phase 3 does not implement matching, notifications, live sources, or automatic applications.
