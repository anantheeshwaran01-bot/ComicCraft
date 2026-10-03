# app/config.py

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# LOAD .ENV
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SETTINGS
# ============================================================

class Settings(BaseSettings):

    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------

    app_name: str = "ComicCraft"

    debug: bool = True


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    gemini_api_key: str = ""

    gemini_flash_model: str = "gemini-3.8-flash"

    gemini_pro_model: str = "gemini-3.8-flash"


    # --------------------------------------------------------
    # IMAGE GENERATION
    # --------------------------------------------------------

    image_provider: str = "cloudflare"

    cloudflare_api_token: str = ""

    cloudflare_account_id: str = ""

    cloudflare_image_model: str = (
        "@cf/black-forest-labs/flux-1-schnell"
    )

    hf_token: str = ""


    # --------------------------------------------------------
    # COMIC SETTINGS
    # --------------------------------------------------------

    panels: int = 5


    # --------------------------------------------------------
    # PROJECT DIRECTORIES
    # --------------------------------------------------------

    base_dir: Path = BASE_DIR

    static_dir: Path = BASE_DIR / "static"

    templates_dir: Path = BASE_DIR / "templates"

    output_dir: Path = BASE_DIR / "output"

    panels_dir: Path = (
        BASE_DIR / "output" / "panels"
    )

    pdf_dir: Path = (
        BASE_DIR / "output" / "pdf"
    )

    exports_dir: Path = (
        BASE_DIR / "output" / "exports"
    )


    # --------------------------------------------------------
    # PYDANTIC SETTINGS CONFIG
    # --------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


    # ========================================================
    # CREATE REQUIRED DIRECTORIES
    # ========================================================

    def ensure_directories(self):
        """Create all directories required by ComicCraft."""

        directories = [
            self.static_dir,
            self.templates_dir,
            self.output_dir,
            self.panels_dir,
            self.pdf_dir,
            self.exports_dir,
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


# ============================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================

settings = Settings()


# ============================================================
# CREATE DIRECTORIES ON IMPORT
# ============================================================

settings.ensure_directories()