import json
import threading
from pathlib import Path

from .helpers import NotFoundError


class JsonStore:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self._lock = threading.Lock()
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if not self.data_file.exists():
            return {"documents": []}
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"documents": []}
        # Accept legacy files that also had topics/files — keep documents only.
        data.setdefault("documents", [])
        return {"documents": data["documents"]}

    def _write(self, data: dict) -> None:
        self.data_file.write_text(
            json.dumps({"documents": data["documents"]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_documents(self) -> list[dict]:
        with self._lock:
            docs = self._read()["documents"]
            return sorted(docs, key=lambda d: d.get("uploadedAt", ""), reverse=True)

    def create_document(self, doc: dict) -> None:
        with self._lock:
            data = self._read()
            data["documents"].append(doc)
            self._write(data)

    def get_document(self, doc_id: str) -> dict:
        with self._lock:
            for doc in self._read()["documents"]:
                if doc["id"] == doc_id:
                    return doc
            raise NotFoundError

    def update_document_type(self, doc_id: str, doc_type: str) -> dict:
        with self._lock:
            data = self._read()
            for doc in data["documents"]:
                if doc["id"] == doc_id:
                    doc["docType"] = doc_type
                    doc["confidence"] = 1.0
                    doc["method"] = "manual"
                    doc["reason"] = "ผู้ใช้กำหนดประเภทเอง"
                    self._write(data)
                    return doc
            raise NotFoundError

    def delete_document(self, doc_id: str) -> dict:
        with self._lock:
            data = self._read()
            deleted = next((d for d in data["documents"] if d["id"] == doc_id), None)
            if not deleted:
                raise NotFoundError
            data["documents"] = [d for d in data["documents"] if d["id"] != doc_id]
            self._write(data)
            return deleted
