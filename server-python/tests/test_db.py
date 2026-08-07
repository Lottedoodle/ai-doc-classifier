import os

import pytest

from app.postgres_store import PostgresStore


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set; skipping database integration test")
    return url


@pytest.fixture
def store() -> PostgresStore:
    return PostgresStore(database_url())


def test_database_connection(store: PostgresStore) -> None:
    with store._connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1


def test_database_documents_table(store: PostgresStore) -> None:
    with store._connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'documents'
                )
                """
            )
            assert cur.fetchone()[0] is True


def test_database_list_documents(store: PostgresStore) -> None:
    docs = store.list_documents()
    assert isinstance(docs, list)
