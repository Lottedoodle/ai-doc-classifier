# Backend setup

```bash
# from repo root
npm run dev:server
# or
cd server-python && python run.py
```

Copy env template:

```bash
cp .env.example .env
```

## Storage modes

| Mode | Metadata | Files |
|---|---|---|
| Local dev | `data.json` | `uploads/` |
| Production | PostgreSQL (`documents` table) | S3 bucket |

Migrations run automatically on startup when `DATABASE_URL` is set.

## Tests

```bash
# from repo root
npm run test:server
```

Integration tests need `DATABASE_URL` pointing to a Postgres instance.
