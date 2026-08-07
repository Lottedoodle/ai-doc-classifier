from pathlib import Path

import psycopg2
import psycopg2.extras

from .helpers import NotFoundError

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATIONS = [
    path.read_text(encoding="utf-8") for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
]

_DOC_COLUMNS = (
    "id, original_name, stored_name, mime_type, size_bytes, "
    "doc_type, confidence, reason, method, uploaded_at"
)


class PostgresStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._migrate()

    def _connect(self):
        return psycopg2.connect(self.database_url)

    def _migrate(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                for migration in MIGRATIONS:
                    cur.execute(migration)
            conn.commit()

    def list_documents(self) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"SELECT {_DOC_COLUMNS} FROM documents ORDER BY uploaded_at DESC"
                )
                return [self._map_document(row) for row in cur.fetchall()]

    def create_document(self, doc: dict) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents
                        (id, original_name, stored_name, mime_type, size_bytes,
                         doc_type, confidence, reason, method, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        doc["id"],
                        doc["originalName"],
                        doc["storedName"],
                        doc["mimeType"],
                        doc["size"],
                        doc["docType"],
                        doc["confidence"],
                        doc["reason"],
                        doc["method"],
                        doc["uploadedAt"],
                    ),
                )
            conn.commit()

    def get_document(self, doc_id: str) -> dict:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"SELECT {_DOC_COLUMNS} FROM documents WHERE id = %s", (doc_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise NotFoundError
                return self._map_document(row)

    def update_document_type(self, doc_id: str, doc_type: str) -> dict:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE documents
                    SET doc_type = %s, confidence = 1.0, method = 'manual',
                        reason = 'ผู้ใช้กำหนดประเภทเอง'
                    WHERE id = %s
                    """,
                    (doc_type, doc_id),
                )
                if cur.rowcount == 0:
                    raise NotFoundError
            conn.commit()
        return self.get_document(doc_id)

    def delete_document(self, doc_id: str) -> dict:
        doc = self.get_document(doc_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            conn.commit()
        return doc

    @staticmethod
    def _map_document(row: dict) -> dict:
        return {
            "id": str(row["id"]),
            "originalName": row["original_name"],
            "storedName": row["stored_name"],
            "mimeType": row["mime_type"],
            "size": int(row["size_bytes"]),
            "docType": row["doc_type"],
            "confidence": float(row["confidence"]),
            "reason": row["reason"] or "",
            "method": row["method"] or "keyword",
            "uploadedAt": _format_ts(row["uploaded_at"]),
        }


def _format_ts(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return str(value)
