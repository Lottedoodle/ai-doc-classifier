import os
import shutil
import tempfile
from pathlib import Path

import boto3


class LocalStorage:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, src_path: Path) -> None:
        dest = self.directory / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest)

    def delete(self, key: str) -> None:
        path = self.directory / key
        if path.exists():
            path.unlink()

    def local_path(self, key: str) -> tuple[Path, callable]:
        return self.directory / key, lambda: None


class S3Storage:
    def __init__(self, bucket: str, region: str) -> None:
        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)

    @staticmethod
    def upload_key(stored_name: str) -> str:
        return f"uploads/{stored_name}"

    def save(self, key: str, src_path: Path, content_type: str) -> None:
        extra = {"ContentType": content_type} if content_type else {}
        self.client.upload_file(str(src_path), self.bucket, key, ExtraArgs=extra)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def local_path(self, key: str) -> tuple[Path, callable]:
        suffix = Path(key).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.close()
        self.client.download_file(self.bucket, key, tmp.name)

        def cleanup() -> None:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

        return Path(tmp.name), cleanup
