
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import router


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="ComicCraft",
    description="AI Comic Generator",
    version="1.0.0",
)


# ============================================================
# DIRECTORIES
# ============================================================

settings.ensure_directories()


# Make sure all required directories exist
PROJECT_ROOT = Path(__file__).resolve().parent.parent

STATIC_DIR = PROJECT_ROOT / "static"
CSS_DIR = STATIC_DIR / "css"

OUTPUT_DIR = PROJECT_ROOT / "output"
PANELS_DIR = OUTPUT_DIR / "panels"
EXPORTS_DIR = OUTPUT_DIR / "exports"


STATIC_DIR.mkdir(parents=True, exist_ok=True)
CSS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PANELS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# STATIC CSS
# ============================================================

app.mount(
    "/static/css",
    StaticFiles(
        directory=str(CSS_DIR)
    ),
    name="css",
)


# ============================================================
# GENERATED PANEL IMAGES
# ============================================================

app.mount(
    "/static/panels",
    StaticFiles(
        directory=str(PANELS_DIR)
    ),
    name="panels",
)


# ============================================================
# GENERATED PDF EXPORTS
# ============================================================

app.mount(
    "/static/exports",
    StaticFiles(
        directory=str(EXPORTS_DIR)
    ),
    name="exports",
)


# ============================================================
# APPLICATION ROUTES
# ============================================================

app.include_router(router)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "app": settings.app_name,
        "panels": settings.panels,
        "image_provider": settings.image_provider,
        "gemini_configured": bool(
            settings.gemini_api_key
        ),
        "huggingface_configured": bool(
            settings.hf_token
        ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": settings.app_name,
        "status": "running",
        "message": "ComicCraft AI Comic Generator is running.",
        "panels": settings.panels,
        "image_provider": settings.image_provider,
    }
