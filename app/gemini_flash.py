import json

from google import genai
from google.genai import types

from app.config import settings


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_client():
    """Create and return the Gemini client."""

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


# ============================================================
# QUOTA ERROR DETECTION
# ============================================================

def is_quota_error(exc: Exception) -> bool:
    """Return True when Gemini reports quota/rate exhaustion."""

    error_text = str(exc).upper()

    return (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "QUOTA" in error_text
        or "RATE LIMIT" in error_text
    )


# ============================================================
# LOCAL 5-PANEL FALLBACK
# ============================================================

def create_fallback_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
):
    """
    Create a complete 5-panel comic outline locally.

    This is used when Gemini is unavailable, especially when
    the daily Gemini API quota has been exhausted.
    """

    return [
        {
            "panel_number": 1,
            "title": "The Beginning",
            "scene_description": (
                f"{character_name} begins the adventure in "
                f"{setting}. The situation from the story "
                f"prompt starts to unfold."
            ),
            "image_prompt": (
                f"{character_name} at the beginning of an "
                f"adventure in {setting}, establishing shot, "
                f"story premise: {story_prompt}, "
                f"{art_style} comic illustration, "
                f"cinematic composition"
            ),
        },
        {
            "panel_number": 2,
            "title": "The Challenge",
            "scene_description": (
                f"{character_name} encounters an important "
                f"challenge related to the story. The "
                f"situation becomes more intense."
            ),
            "image_prompt": (
                f"{character_name} facing the main challenge "
                f"of the story in {setting}, dramatic moment, "
                f"strong facial expression, "
                f"{art_style} comic illustration, "
                f"cinematic lighting"
            ),
        },
        {
            "panel_number": 3,
            "title": "The Turning Point",
            "scene_description": (
                f"{character_name} takes action and moves "
                f"deeper into the adventure. The story "
                f"reaches its turning point."
            ),
            "image_prompt": (
                f"{character_name} taking decisive action "
                f"during the adventure in {setting}, "
                f"dynamic action scene, "
                f"dramatic perspective, "
                f"{art_style} comic illustration"
            ),
        },
        {
            "panel_number": 4,
            "title": "The Discovery",
            "scene_description": (
                f"{character_name} discovers something important "
                f"that changes the direction of the story."
            ),
            "image_prompt": (
                f"{character_name} discovering something "
                f"important in {setting}, sense of wonder, "
                f"dramatic discovery, detailed environment, "
                f"{art_style} comic illustration, "
                f"cinematic composition"
            ),
        },
        {
            "panel_number": 5,
            "title": "The Ending",
            "scene_description": (
                f"{character_name} reaches the conclusion "
                f"of the adventure. The experience leaves "
                f"a memorable final moment."
            ),
            "image_prompt": (
                f"{character_name} at the conclusion of the "
                f"adventure in {setting}, heroic final scene, "
                f"emotional ending, cinematic composition, "
                f"{art_style} comic illustration"
            ),
        },
    ]


# ============================================================
# GEMINI OUTLINE GENERATION
# ============================================================

def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
):
    """
    Generate a structured 5-panel comic outline.

    If Gemini quota is exhausted, automatically falls back
    to a local 5-panel outline.
    """

    prompt = f"""
Create a comic story outline with EXACTLY 5 panels.

STORY:
{story_prompt}

MAIN CHARACTER:
{character_name}

SETTING:
{setting}

TONE:
{tone}

ART STYLE:
{art_style}

For every panel provide:

panel_number
title
scene_description
image_prompt

Rules:

- Exactly 5 panels.
- Panel numbers must be 1, 2, 3, 4, 5.
- Maintain continuity.
- The main character must remain consistent.
- The setting must remain consistent.
- image_prompt must describe only visual content.
- Do not include dialogue in image_prompt.
- Do not include text inside the generated image.
- Return ONLY valid JSON.

JSON format:

[
    {{
        "panel_number": 1,
        "title": "...",
        "scene_description": "...",
        "image_prompt": "..."
    }}
]
"""

    try:

        print()
        print(
            f"Gemini outline generation using "
            f"{settings.gemini_flash_model}..."
        )

        client = get_client()

        response = client.models.generate_content(
            model=settings.gemini_flash_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=3000,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty outline."
            )

        data = json.loads(
            response.text
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "Gemini outline response is not a list."
            )

        # ----------------------------------------------------
        # Normalize to exactly 5 panels
        # ----------------------------------------------------

        panels = []

        for index, panel in enumerate(data[:5], start=1):

            panels.append(
                {
                    "panel_number": index,
                    "title": str(
                        panel.get(
                            "title",
                            f"Panel {index}",
                        )
                    ),
                    "scene_description": str(
                        panel.get(
                            "scene_description",
                            "",
                        )
                    ),
                    "image_prompt": str(
                        panel.get(
                            "image_prompt",
                            "",
                        )
                    ),
                }
            )

        if len(panels) != 5:
            raise RuntimeError(
                "Gemini did not return exactly 5 panels."
            )

        print(
            "Successfully generated 5 comic panels."
        )

        return panels

    except Exception as exc:

        print()
        print("=" * 60)
        print("GEMINI OUTLINE GENERATION FAILED")
        print("=" * 60)
        print(str(exc))
        print("=" * 60)

        if is_quota_error(exc):

            print(
                "Gemini daily quota is exhausted."
            )

            print(
                "Using LOCAL 5-PANEL OUTLINE FALLBACK."
            )

        else:

            print(
                "Gemini outline generation failed."
            )

            print(
                "Using LOCAL 5-PANEL OUTLINE FALLBACK."
            )

        fallback = create_fallback_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        print(
            "Successfully created 5-panel "
            "fallback outline."
        )

        return fallback