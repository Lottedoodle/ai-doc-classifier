from datetime import datetime, timezone


class StoreError(Exception):
    pass


class NotFoundError(StoreError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
