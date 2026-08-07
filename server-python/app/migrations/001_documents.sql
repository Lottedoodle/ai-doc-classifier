-- migrations/001_documents.sql
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    doc_type TEXT NOT NULL CHECK (doc_type IN ('purchase_order', 'invoice', 'receipt', 'general')),
    confidence REAL NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    method TEXT NOT NULL DEFAULT 'keyword',
    uploaded_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS documents_doc_type_idx ON documents (doc_type);
CREATE INDEX IF NOT EXISTS documents_uploaded_at_idx ON documents (uploaded_at DESC);
