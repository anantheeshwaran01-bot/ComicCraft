
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


# ============================================================
# STATIC FILE DIRECTORIES
# ============================================================

# Project structure:
#
# comiccraft/
#
# ├── app/
# │
# ├── static/
# │   └── css/
# │       └── style.css
# │
# ├── templates/
# │   ├── index.html
# │   ├── comic_preview.html
# │   └── export_success.html
# │
# └── output/
#     ├── panels/
#     │   ├── panel_1_xxxxx.png
#     │   ├── panel_2_xxxxx.png
#     │   └── ...
#     │
#     └── exports/
#         └── comic.pdf
#
#
# URL mapping:
#
# /static/css/style.css
#       ↓
# static/css/style.css
#
# /static/panels/panel_1.png
#       ↓
# output/panels/panel_1.png
#
# /static/exports/comic.pdf
#       ↓
# output/exports/comic.pdf


# ============================================================
# CSS
# ============================================================

app.mount(
    "/static/css",
    StaticFiles(
        directory=str(
            settings.static_dir / "css"
        )
    ),
    name="css",
)


# ============================================================
# GENERATED PANEL IMAGES
# ============================================================

app.mount(
    "/static/panels",
    StaticFiles(
        directory=str(
            settings.panels_dir
        )
    ),
    name="panels",
)


# ============================================================
# GENERATED PDF EXPORTS
# ============================================================

app.mount(
    "/static/exports",
    StaticFiles(
        directory=str(
            settings.exports_dir
        )
    ),
    name="exports",
)


# ============================================================
# API / HTML ROUTES
# ============================================================

app.include_router(router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": settings.app_name,
        "status": "running",
        "panels": settings.panels,
        "image_provider": settings.image_provider,
    }
