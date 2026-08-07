import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .auth import require_user
from .classifier import DOC_TYPES, classify_document
from .file_storage import S3Storage
from .helpers import NotFoundError, now_iso
from .ocr import extract_text_from_file

router = APIRouter()

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}


def _mime_from_ext(ext: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")


def _decode_filename(name: str) -> str:
    if not name:
        return name
    try:
        return name.encode("latin1").decode("utf-8")
    except UnicodeError:
        return name


from .state import AppState


def file_key(stored_name: str) -> str:
    if AppState.use_s3:
        return S3Storage.upload_key(stored_name)
    return stored_name


@router.get("/doc-types")
def list_doc_types():
    from .classifier import DOC_TYPE_LABELS

    return [
        {"id": key, "label": DOC_TYPE_LABELS[key]}
        for key in DOC_TYPES
    ]


@router.get("/documents")
def list_documents(_user=Depends(require_user)):
    return AppState.store.list_documents()


@router.post("/documents", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    originalName: str = Form(""),
    _user=Depends(require_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, {"error": "รองรับเฉพาะไฟล์ JPG, PNG, GIF, WEBP, PDF"})

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, {"error": "ไฟล์ใหญ่เกิน 10MB"})

    stored_name = f"{uuid.uuid4()}{ext}"
    content_type = file.content_type or _mime_from_ext(ext)
    original = originalName.strip() or _decode_filename(file.filename or "")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        try:
            text = extract_text_from_file(tmp_path, content_type)
        except Exception as exc:
            print(f"text extraction failed: {exc}")
            text = ""

        result = classify_document(text, original, AppState.ai_settings)

        key = file_key(stored_name)
        if AppState.use_s3:
            AppState.files.save(key, tmp_path, content_type)
        else:
            AppState.files.save(key, tmp_path)

        record = {
            "id": str(uuid.uuid4()),
            "originalName": original,
            "storedName": stored_name,
            "mimeType": content_type,
            "size": len(content),
            "docType": result.doc_type,
            "confidence": result.confidence,
            "reason": result.reason,
            "method": result.method,
            "uploadedAt": now_iso(),
        }
        AppState.store.create_document(record)
        return record
    except HTTPException:
        raise
    except Exception:
        AppState.files.delete(file_key(stored_name))
        raise
    finally:
        tmp_path.unlink(missing_ok=True)


@router.patch("/documents/{doc_id}")
def update_document(doc_id: str, body: dict, _user=Depends(require_user)):
    doc_type = (body.get("docType") or "").strip()
    if doc_type not in DOC_TYPES:
        raise HTTPException(400, {"error": f"docType must be one of {', '.join(DOC_TYPES)}"})
    try:
        return AppState.store.update_document_type(doc_id, doc_type)
    except NotFoundError:
        raise HTTPException(404, {"error": "Document not found"})


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, _user=Depends(require_user)):
    try:
        record = AppState.store.delete_document(doc_id)
    except NotFoundError:
        raise HTTPException(404, {"error": "Document not found"})
    AppState.files.delete(file_key(record["storedName"]))
    return {"ok": True}
