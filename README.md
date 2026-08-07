# AI Document Classifier

เว็บแอปสำหรับอัปโหลดเอกสารแล้วให้ AI จำแนกประเภทอัตโนมัติเป็น 4 ประเภท:

- **PO** — ใบสั่งซื้อ (Purchase Order)
- **Invoice** — ใบแจ้งหนี้ / ใบกำกับภาษี
- **Receipt** — ใบเสร็จรับเงิน
- **General** — เอกสารทั่วไป

## Quick start

```bash
npm install
cp server-python/.env.example server-python/.env   # แล้วแก้ค่าตามต้องการ
npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:3001

## โครงสร้างโปรเจกต์

```
├── src/                    # React frontend (Vite + Tailwind)
│   ├── pages/              # UploadPage, DashboardPage
│   ├── components/         # DropZone, DocumentCard
│   ├── api.js              # API client
│   └── docTypes.js         # UI config สำหรับ 4 ประเภท
├── server-python/          # FastAPI backend
│   ├── run.py              # dev entry point
│   └── app/
│       ├── main.py         # FastAPI app factory
│       ├── routes.py       # REST API (/api/documents)
│       ├── classifier.py   # Bedrock / OpenAI + keyword fallback
│       ├── ocr.py          # PDF + Tesseract text extraction
│       ├── json_store.py   # local metadata (dev)
│       ├── postgres_store.py
│       ├── file_storage.py # local uploads / S3
│       └── migrations/
├── scripts/                # AWS deploy helpers (ops)
└── Dockerfile              # production backend image
```

## Environment variables

ดูรายละเอียดครบใน `server-python/.env.example`

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | production | PostgreSQL สำหรับ metadata |
| `S3_BUCKET` | yes | เก็บไฟล์เอกสารที่ upload (default: `classify-docs-047750375159-ap-southeast-2-an`) |
| `AWS_REGION` | yes (Bedrock) | default `ap-southeast-2` |
| `AI_PROVIDER` | no | `bedrock` (default) หรือ `openai` |
| `AI_MODEL` | no | default `amazon.nova-lite-v1:0` |

Local dev: ปล่อย `DATABASE_URL` และ `S3_BUCKET` ว่าง → ใช้ `data.json` + `server-python/uploads/`

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Frontend + backend |
| `npm run build` | Build frontend → `dist/` |
| `npm run test:server` | pytest |
| `npm run db:check` | ทดสอบเชื่อมต่อ Postgres |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/documents` | รายการเอกสาร |
| POST | `/api/documents` | upload + classify |
| PATCH | `/api/documents/{id}` | เปลี่ยนประเภท |
| DELETE | `/api/documents/{id}` | ลบเอกสาร |
| GET | `/api/doc-types` | รายการประเภทที่รองรับ |
| GET | `/uploads/{file}` | เปิดไฟล์ที่ upload |
