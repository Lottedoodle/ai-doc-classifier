import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Config
from app.postgres_store import PostgresStore


def main() -> None:
    cfg = Config()
    if not cfg.database_url:
        print("DATABASE_URL is not set (check server-python/.env)", file=sys.stderr)
        sys.exit(1)
    try:
        store = PostgresStore(cfg.database_url)
        docs = store.list_documents()
    except Exception as exc:
        print(f"connect failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print("Database connection OK")
    print(f"documents table readable; count = {len(docs)}")


if __name__ == "__main__":
    main()
