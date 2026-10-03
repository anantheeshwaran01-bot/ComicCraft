
import traceback
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.schemas import PromptRequest

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


router = APIRouter()

templates = Jinja2Templates(
    directory=str(settings.templates_dir)
)


# ============================================================
# IMAGE URL NORMALIZER
# ============================================================

def normalize_image_url(image_url: str) -> str:
    """
    Convert any generated image path into a browser-accessible
    /static/panels/<filename> URL.

    Examples:

        /static/panels/panel_1_xxx.png
        output/panels/panel_1_xxx.png
        C:/project/output/panels/panel_1_xxx.png

    all become:

        /static/panels/panel_1_xxx.png
    """

    if not image_url:
        return ""

    image_url = str(image_url).replace("\\", "/")

    # Already correct
    if image_url.startswith("/static/panels/"):
        return image_url

    # If a full URL was returned, keep it.
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url

    filename = Path(image_url).name

    return f"/static/panels/{filename}"


# ============================================================
# PDF URL NORMALIZER
# ============================================================

def normalize_pdf_url(pdf_url: str) -> str:
    """
    Convert local PDF path into browser-accessible URL.
    """

    if not pdf_url:
        return ""

    pdf_url = str(pdf_url).replace("\\", "/")

    if pdf_url.startswith("/static/"):
        return pdf_url

    if pdf_url.startswith("http://") or pdf_url.startswith("https://"):
        return pdf_url

    filename = Path(pdf_url).name

    return f"/static/exports/{filename}"


# ============================================================
# VERIFY GENERATED IMAGE
# ============================================================

def verify_image_exists(image_url: str) -> bool:
    """
    Verify that the image actually exists in output/panels.
    """

    if not image_url:
        return False

    filename = Path(image_url).name

    image_path = settings.panels_dir / filename

    exists = image_path.exists()

    print()
    print("IMAGE VERIFICATION")
    print("-" * 50)
    print(f"URL      : {image_url}")
    print(f"FILE     : {image_path}")
    print(f"EXISTS   : {exists}")
    print("-" * 50)

    return exists


# ============================================================
# COMPLETE COMIC GENERATION PIPELINE
# ============================================================

def generate_comic(payload: PromptRequest):

    print()
    print("=" * 60)
    print("STARTING COMIC GENERATION")
    print("=" * 60)

    # ========================================================
    # STEP 1: OUTLINE
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 1: GENERATING COMIC OUTLINE")
    print("=" * 60)

    outline = generate_outline(
        payload.story_prompt,
        payload.character_name,
        payload.setting,
        payload.tone,
        payload.art_style,
    )

    if not outline:
        raise RuntimeError(
            "Comic outline generation returned no panels."
        )

    outline = outline[:5]

    if len(outline) != 5:
        raise RuntimeError(
            f"Comic outline must contain exactly 5 panels. "
            f"Received {len(outline)}."
        )

    print("✓ Outline ready: 5 panels")

    # ========================================================
    # STEP 2: STORY
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 2: GENERATING PANEL STORY")
    print("=" * 60)

    stories = generate_story(
        outline,
        payload.character_name,
        payload.tone,
    )

    if not stories:
        raise RuntimeError(
            "Comic story generation returned no panels."
        )

    stories = stories[:5]

    if len(stories) != 5:
        raise RuntimeError(
            f"Comic story must contain exactly 5 panels. "
            f"Received {len(stories)}."
        )

    print("✓ Story ready: 5 panels")

    # ========================================================
    # STEP 3: IMAGE GENERATION
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 3: GENERATING PANEL IMAGES")
    print("=" * 60)

    image_urls = []

    for panel in outline:

        panel_number = panel["panel_number"]

        print(
            f"Generating image for panel "
            f"{panel_number}/5..."
        )

        image_prompt = (
            f"{panel['image_prompt']}. "
            f"Visual style: {payload.art_style}. "
            f"Setting: {payload.setting}. "
            f"Main character: {payload.character_name}. "
            "Professional comic illustration, "
            "cinematic composition, "
            "consistent character appearance, "
            "high quality, "
            "no text, "
            "no watermark."
        )

        raw_image_url = generate_image(
            image_prompt,
            panel_number,
        )

        if not raw_image_url:
            raise RuntimeError(
                f"Image generation failed for "
                f"panel {panel_number}."
            )

        # Normalize URL
        image_url = normalize_image_url(
            raw_image_url
        )

        # Verify physical file
        if not verify_image_exists(image_url):

            print()
            print(
                f"WARNING: Image file was not found:"
            )
            print(image_url)

            # Try finding matching panel file
            matching_files = list(
                settings.panels_dir.glob(
                    f"panel_{panel_number}_*.png"
                )
            )

            if matching_files:

                latest_file = max(
                    matching_files,
                    key=lambda p: p.stat().st_mtime,
                )

                image_url = (
                    f"/static/panels/"
                    f"{latest_file.name}"
                )

                print(
                    "✓ Found matching image:"
                )
                print(
                    latest_file
                )

            else:

                raise RuntimeError(
                    f"Generated image for panel "
                    f"{panel_number} does not exist "
                    f"in {settings.panels_dir}"
                )

        image_urls.append(image_url)

        print(
            f"✓ Panel {panel_number} image ready"
        )
        print(
            f"  URL: {image_url}"
        )

    if len(image_urls) != 5:
        raise RuntimeError(
            "Exactly 5 panel images are required."
        )

    print()
    print("✓ All 5 panel images generated")

    # ========================================================
    # STEP 4: BUILD LAYOUT
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 4: BUILDING COMIC LAYOUT")
    print("=" * 60)

    layout = build_comic_layout(
        outline,
        stories,
        image_urls,
    )

    if not layout:
        raise RuntimeError(
            "Comic layout generation returned no data."
        )

    print("✓ Comic layout created")

    # ========================================================
    # STEP 5: TITLE
    # ========================================================

    clean_prompt = (
        payload.story_prompt
        .replace("\n", " ")
        .strip()
    )

    title = (
        f"{payload.character_name}: "
        f"{clean_prompt[:55]}"
    )

    # ========================================================
    # STEP 6: PDF
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 5: EXPORTING PDF")
    print("=" * 60)

    pdf_url = save_pdf(
        layout,
        title,
    )

    if not pdf_url:
        raise RuntimeError(
            "PDF export failed."
        )

    pdf_url = normalize_pdf_url(
        pdf_url
    )

    print(
        f"✓ PDF exported successfully"
    )

    print(
        f"PDF URL: {pdf_url}"
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 60)
    print("🎉 COMIC GENERATION COMPLETE")
    print("=" * 60)
    print("✓ 5 panels")
    print("✓ 5 images")
    print("✓ Comic layout")
    print("✓ PDF")
    print("=" * 60)

    return (
        title,
        layout,
        pdf_url,
    )


# ============================================================
# HOME
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "error": None,
        },
    )


# ============================================================
# GENERATE COMIC - HTML
# ============================================================

@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate_form(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),
):

    try:

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not story_prompt.strip():
            raise ValueError(
                "Story prompt cannot be empty."
            )

        if not character_name.strip():
            raise ValueError(
                "Character name cannot be empty."
            )

        if not setting.strip():
            raise ValueError(
                "Setting cannot be empty."
            )

        if not tone.strip():
            raise ValueError(
                "Tone cannot be empty."
            )

        if not art_style.strip():
            raise ValueError(
                "Art style cannot be empty."
            )

        # ----------------------------------------------------
        # CREATE PAYLOAD
        # ----------------------------------------------------

        payload = PromptRequest(
            story_prompt=story_prompt.strip(),
            character_name=character_name.strip(),
            setting=setting.strip(),
            tone=tone.strip(),
            art_style=art_style.strip(),
        )

        # ----------------------------------------------------
        # GENERATE
        # ----------------------------------------------------

        title, layout, pdf_url = generate_comic(
            payload
        )

        # ----------------------------------------------------
        # RENDER RESULT
        # ----------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "title": title,
                "layout": layout,
                "pdf_url": pdf_url,
            },
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("COMIC GENERATION ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70)
        print(
            f"ERROR TYPE: {type(exc).__name__}"
        )
        print(
            f"ERROR MESSAGE: {exc}"
        )
        print("=" * 70)

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "app_name": settings.app_name,
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            },
            status_code=500,
        )


# ============================================================
# JSON API
# ============================================================

@router.post(
    "/generate-comic/json"
)
async def generate_json(
    payload: PromptRequest,
):

    try:

        title, layout, pdf_url = generate_comic(
            payload
        )

        return {
            "success": True,
            "title": title,
            "panels": layout,
            "pdf_url": pdf_url,
        }

    except Exception as exc:

        print()
        print("=" * 70)
        print("JSON COMIC GENERATION ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            },
        )


# ============================================================
# TEST IMAGE
# ============================================================

@router.post(
    "/test-image"
)
async def test_image(
    prompt: str = Form(...),
):

    try:

        if not prompt.strip():
            raise ValueError(
                "Image prompt cannot be empty."
            )

        raw_image_url = generate_image(
            prompt.strip(),
            0,
        )

        if not raw_image_url:
            raise RuntimeError(
                "Image generation returned no image."
            )

        image_url = normalize_image_url(
            raw_image_url
        )

        return {
            "success": True,
            "image_url": image_url,
        }

    except Exception as exc:

        print()
        print("=" * 70)
        print("IMAGE GENERATION ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            },
        )


# ============================================================
# EXPORT SUCCESS
# ============================================================

@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={},
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get(
    "/health"
)
async def health():

    return {
        "status": "ok",

        "gemini_configured":
            bool(
                settings.gemini_api_key
            ),

        "huggingface_configured":
            bool(
                settings.hf_token
            ),

        "cloudflare_configured":
            bool(
                settings.cloudflare_api_token
            ),

        "image_provider":
            settings.image_provider,

        "gemini_flash_model":
            settings.gemini_flash_model,

        "gemini_story_model":
            settings.gemini_pro_model,

        "panels":
            settings.panels,

        "output_directory":
            str(settings.output_dir),

        "panels_directory":
            str(settings.panels_dir),
    }