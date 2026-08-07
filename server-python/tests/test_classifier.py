import os
import tempfile
from pathlib import Path

import pytest

from app.classifier import AISettings, classify_document
from app.json_store import JsonStore


def test_keyword_classifier_purchase_order():
    settings = AISettings(provider="openai", api_key="", model="", base_url="")
    result = classify_document(
        "Purchase Order PO-20170001 vendor delivery",
        "po.pdf",
        settings,
    )
    assert result.doc_type == "purchase_order"
    assert result.method == "keyword"
    assert 0.0 < result.confidence <= 1.0


def test_keyword_classifier_general():
    settings = AISettings(provider="openai", api_key="", model="", base_url="")
    result = classify_document("รายงานการประชุมประจำเดือน", "memo.pdf", settings)
    assert result.doc_type == "general"
    assert result.method == "keyword"


def test_json_store_documents_crud():
    data_file = Path(tempfile.mkdtemp()) / "data.json"
    store = JsonStore(data_file)
    doc = {
        "id": "d1",
        "originalName": "test.pdf",
        "storedName": "abc.pdf",
        "mimeType": "application/pdf",
        "size": 1,
        "docType": "invoice",
        "confidence": 0.8,
        "reason": "test",
        "method": "keyword",
        "uploadedAt": "2026-01-01T00:00:00.000Z",
    }
    store.create_document(doc)
    assert len(store.list_documents()) == 1
    updated = store.update_document_type("d1", "receipt")
    assert updated["docType"] == "receipt"
    assert updated["method"] == "manual"
    deleted = store.delete_document("d1")
    assert deleted["id"] == "d1"
    assert store.list_documents() == []
