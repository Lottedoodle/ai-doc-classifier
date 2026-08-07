from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .classifier import AISettings
from .config import Config
from .file_storage import LocalStorage, S3Storage
from .json_store import JsonStore
from .postgres_store import PostgresStore
from .routes import router
from .state import AppState


def create_app() -> FastAPI:
    cfg = Config()

    if cfg.use_postgres:
        AppState.store = PostgresStore(cfg.database_url)
    else:
        AppState.store = JsonStore(cfg.data_file)

    if cfg.use_s3:
        AppState.files = S3Storage(cfg.s3_bucket, cfg.aws_region)
        AppState.use_s3 = True
    else:
        AppState.files = LocalStorage(cfg.uploads_dir)
        AppState.use_s3 = False

    AppState.ai_settings = AISettings(
        provider=cfg.ai_provider,
        api_key=cfg.ai_api_key,
        model=cfg.ai_model,
        base_url=cfg.ai_base_url,
        region=cfg.bedrock_region,
        timeout=cfg.ai_timeout,
    )

    AppState.auth_enabled = cfg.auth_enabled
    AppState.supabase_url = cfg.supabase_url
    AppState.supabase_anon_key = cfg.supabase_anon_key

    app = FastAPI(title="AI Document Classifier")

    @app.get("/health")
    def health():
        return {"ok": True}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")

    if AppState.use_s3:
        from pathlib import Path

        from fastapi.responses import FileResponse
        from starlette.background import BackgroundTask

        from .routes import _mime_from_ext, file_key

        @app.get("/uploads/{path:path}")
        def serve_upload(path: str):
            local, cleanup = AppState.files.local_path(file_key(path))
            return FileResponse(
                local,
                media_type=_mime_from_ext(Path(path).suffix.lower()),
                background=BackgroundTask(cleanup),
            )
    else:
        app.mount("/uploads", StaticFiles(directory=str(cfg.uploads_dir)), name="uploads")

    mode = "local"
    if cfg.use_postgres:
        mode = "postgres"
    if cfg.use_s3:
        mode += "+s3"
    if AppState.ai_settings.enabled:
        ai_mode = f"{AppState.ai_settings.provider}:{AppState.ai_settings.model}"
    else:
        ai_mode = "keyword-fallback"
    auth_mode = "auth" if AppState.auth_enabled else "no-auth"
    print(f"Server ready ({mode}, classifier: {ai_mode}, {auth_mode})")

    return app


app = create_app()


def main() -> None:
    import uvicorn
    from pathlib import Path

    cfg = Config()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=cfg.port,
        reload=cfg.reload,
        reload_dirs=[str(Path(__file__).resolve().parent)],
    )


if __name__ == "__main__":
    main()
