"""AI document classifier.

Classifies a document into one of 4 types:
  - purchase_order : ใบสั่งซื้อ (PO)
  - invoice        : ใบแจ้งหนี้ / ใบกำกับภาษี (Invoice)
  - receipt        : ใบเสร็จรับเงิน (Receipt)
  - general        : เอกสารทั่วไป

Providers (AI_PROVIDER in .env):
  - "bedrock" (default) : Amazon Bedrock Converse API via AWS credentials
                          (e.g. amazon.nova-lite-v1:0 in ap-southeast-2)
  - "openai"            : any OpenAI-compatible Chat Completions API (needs AI_API_KEY)

Falls back to keyword-based scoring when the AI call fails or is not
configured, so the app keeps working.
"""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

DOC_TYPES = ("purchase_order", "invoice", "receipt", "general")

DOC_TYPE_LABELS = {
    "purchase_order": "ใบสั่งซื้อ (PO)",
    "invoice": "ใบแจ้งหนี้ (Invoice)",
    "receipt": "ใบเสร็จรับเงิน (Receipt)",
    "general": "เอกสารทั่วไป",
}

# Keyword patterns per type used by the fallback classifier.
_KEYWORDS = {
    "purchase_order": [
        r"purchase\s*order", r"\bp\.?\s*o\.?\s*(no|number|#)", r"ใบสั่งซื้อ",
        r"ใบขอซื้อ", r"vendor", r"ผู้ขาย", r"สั่งซื้อ", r"delivery\s*date",
        r"กำหนดส่งมอบ", r"\bpo\b",
    ],
    "invoice": [
        r"\binvoice\b", r"ใบแจ้งหนี้", r"ใบกำกับภาษี", r"ใบวางบิล", r"tax\s*invoice",
        r"due\s*date", r"ครบกำหนดชำระ", r"invoice\s*(no|number|#)", r"เลขที่ใบแจ้งหนี้",
        r"billing", r"วางบิล",
    ],
    "receipt": [
        r"\breceipt\b", r"ใบเสร็จ", r"ใบเสร็จรับเงิน", r"received\s*from", r"ได้รับเงิน",
        r"ชำระเงินแล้ว", r"ชำระแล้ว", r"\bpaid\b", r"เงินสด", r"รับเงิน",
        r"payment\s*received", r"สลิป", r"slip", r"โอนเงิน",
    ],
}

_SYSTEM_PROMPT = """คุณเป็นระบบจำแนกประเภทเอกสารทางธุรกิจ
จงจำแนกเอกสารเป็น 1 ใน 4 ประเภทนี้เท่านั้น:
- purchase_order : ใบสั่งซื้อ (PO)
- invoice        : ใบแจ้งหนี้ / ใบกำกับภาษี / ใบวางบิล
- receipt        : ใบเสร็จรับเงิน / สลิปโอนเงิน / หลักฐานการชำระเงิน
- general        : เอกสารทั่วไปที่ไม่เข้าข่ายข้างต้น

ตอบเป็น JSON เท่านั้น รูปแบบ:
{"doc_type": "<ประเภท>", "confidence": <0.0-1.0>, "reason": "<เหตุผลสั้น ๆ ภาษาไทย>"}"""


@dataclass
class ClassificationResult:
    doc_type: str = "general"
    confidence: float = 0.0
    reason: str = ""
    method: str = "keyword"  # "ai" or "keyword"


@dataclass
class AISettings:
    provider: str = "bedrock"  # "bedrock" or "openai"
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    region: str = "ap-southeast-2"
    timeout: int = 30

    @property
    def enabled(self) -> bool:
        if self.provider == "bedrock":
            return bool(self.model and self.region)
        return bool(self.api_key and self.model and self.base_url)


def classify_document(text: str, filename: str, settings: AISettings) -> ClassificationResult:
    """Classify document text into one of DOC_TYPES."""
    if settings.enabled:
        try:
            if settings.provider == "bedrock":
                return _classify_with_bedrock(text, filename, settings)
            return _classify_with_openai(text, filename, settings)
        except Exception as exc:  # noqa: BLE001 — fall back on any AI failure
            print(f"AI classification failed ({settings.provider}), falling back to keywords: {exc}")
    return _classify_with_keywords(text, filename)


def _build_user_content(text: str, filename: str) -> str:
    snippet = (text or "").strip()[:6000]
    return f"ชื่อไฟล์: {filename}\n\nข้อความในเอกสาร:\n{snippet or '(อ่านข้อความไม่ได้)'}"


def _parse_ai_json(content: str) -> ClassificationResult:
    """Parse the model's JSON answer (tolerates code fences / surrounding text)."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    parsed = json.loads(match.group(0) if match else cleaned)

    doc_type = parsed.get("doc_type", "general")
    if doc_type not in DOC_TYPES:
        doc_type = "general"
    try:
        confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0))))
    except (TypeError, ValueError):
        confidence = 0.0

    return ClassificationResult(
        doc_type=doc_type,
        confidence=confidence,
        reason=str(parsed.get("reason", "")).strip(),
        method="ai",
    )


def _classify_with_bedrock(text: str, filename: str, settings: AISettings) -> ClassificationResult:
    import boto3
    from botocore.config import Config as BotoConfig

    client = boto3.client(
        "bedrock-runtime",
        region_name=settings.region,
        config=BotoConfig(read_timeout=settings.timeout, connect_timeout=10),
    )
    response = client.converse(
        modelId=settings.model,
        system=[{"text": _SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": _build_user_content(text, filename)}]}],
        inferenceConfig={"temperature": 0, "maxTokens": 300},
    )
    content = response["output"]["message"]["content"][0]["text"]
    return _parse_ai_json(content)


def _classify_with_openai(text: str, filename: str, settings: AISettings) -> ClassificationResult:
    payload = {
        "model": settings.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_content(text, filename)},
        ],
    }
    req = urllib.request.Request(
        f"{settings.base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=settings.timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    return _parse_ai_json(content)


def _classify_with_keywords(text: str, filename: str) -> ClassificationResult:
    haystack = f"{filename}\n{text or ''}".lower()

    scores = {}
    matched = {}
    for doc_type, patterns in _KEYWORDS.items():
        hits = [p for p in patterns if re.search(p, haystack)]
        scores[doc_type] = len(hits)
        matched[doc_type] = hits

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return ClassificationResult(
            doc_type="general",
            confidence=0.3,
            reason="ไม่พบคำสำคัญของ PO / Invoice / ใบเสร็จ จึงจัดเป็นเอกสารทั่วไป",
            method="keyword",
        )

    confidence = min(0.5 + best_score * 0.1, 0.9)
    return ClassificationResult(
        doc_type=best_type,
        confidence=round(confidence, 2),
        reason=f"พบคำสำคัญของ{DOC_TYPE_LABELS[best_type]} {best_score} รายการ",
        method="keyword",
    )
