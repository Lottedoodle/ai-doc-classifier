import os
from pathlib import Path

from dotenv import load_dotenv

WEB_ROOT = Path(__file__).resolve().parents[2]
SERVER_DIR = WEB_ROOT / "server-python"
DEFAULT_DATA = SERVER_DIR / "data.json"
DEFAULT_UPLOADS = SERVER_DIR / "uploads"

load_dotenv(SERVER_DIR / ".env", override=True)


class Config:
    def __init__(self) -> None:
        self.port = int(os.getenv("PORT", "3001"))
        self.database_url = os.getenv("DATABASE_URL", "")
        self.s3_bucket = os.getenv("S3_BUCKET", "")
        self.aws_region = os.getenv("AWS_REGION", "ap-southeast-2")
        self.data_file = Path(os.getenv("DATA_FILE", str(DEFAULT_DATA)))
        self.uploads_dir = Path(os.getenv("UPLOADS_DIR", str(DEFAULT_UPLOADS)))
        self.reload = os.getenv("RELOAD", "1") == "1"

        self.ai_provider = os.getenv("AI_PROVIDER", "bedrock").strip().lower()
        self.ai_model = os.getenv("AI_MODEL", "amazon.nova-lite-v1:0")
        self.bedrock_region = os.getenv("BEDROCK_REGION", "") or self.aws_region
        self.ai_api_key = os.getenv("AI_API_KEY", "")
        self.ai_base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
        self.ai_timeout = int(os.getenv("AI_TIMEOUT", "30"))

        self.supabase_url = (
            os.getenv("SUPABASE_URL")
            or os.getenv("VITE_SUPABASE_URL")
            or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            or ""
        )
        self.supabase_anon_key = (
            os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("VITE_SUPABASE_ANON_KEY")
            or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
            or ""
        )

    @property
    def auth_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def use_postgres(self) -> bool:
        return bool(self.database_url)

    @property
    def use_s3(self) -> bool:
        return bool(self.s3_bucket)
