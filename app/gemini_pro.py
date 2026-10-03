
import json

from google import genai
from google.genai import types

from app.config import settings
from app.schemas import PanelStory


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
    """Detect Gemini quota/rate-limit errors."""

    error_text = str(exc).upper()

    return (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "QUOTA" in error_text
        or "RATE LIMIT" in error_text
    )


# ============================================================
# LOCAL STORY FALLBACK
# ============================================================

def create_fallback_story(
    outline,
    character_name: str,
    tone: str,
):
    """
    Create a complete 5-panel story locally.

    This allows ComicCraft to continue working even when
    Gemini's daily API quota has been exhausted.
    """

    stories = []

    fallback_dialogues = [
        f"{character_name}: Something is about to begin.",
        f"{character_name}: I have to keep going.",
        f"{character_name}: There is no turning back now.",
        f"{character_name}: I finally understand.",
        f"{character_name}: What an incredible journey.",
    ]

    fallback_captions = [
        "THE ADVENTURE BEGINS...",
        "A NEW CHALLENGE!",
        "THE TURNING POINT!",
        "A STRANGE DISCOVERY...",
        "THE END... FOR NOW.",
    ]

    for index, panel in enumerate(outline[:5]):

        panel_number = index + 1

        scene_description = str(
            panel.get(
                "scene_description",
                "The story continues.",
            )
        )

        narration = (
            f"{scene_description} "
            f"{character_name} continues the adventure "
            f"with determination."
        )

        # Make the final panel feel like a conclusion.
        if panel_number == 5:
            narration = (
                f"{scene_description} "
                f"{character_name} reaches the end of "
                f"this memorable journey."
            )

        story = {
            "panel_number": panel_number,
            "narration": narration,
            "dialogue": fallback_dialogues[index],
            "caption": fallback_captions[index],
        }

        stories.append(story)

    # Guarantee exactly five panels.
    while len(stories) < 5:

        index = len(stories)

        stories.append(
            {
                "panel_number": index + 1,
                "narration": (
                    f"{character_name} continues the story "
                    "and moves toward the conclusion."
                ),
                "dialogue": (
                    f"{character_name}: Let's keep moving."
                ),
                "caption": "THE STORY CONTINUES...",
            }
        )

    return stories[:5]


# ============================================================
# GEMINI STORY GENERATION
# ============================================================

def generate_story(
    outline,
    character_name: str,
    tone: str,
):
    """
    Generate panel-by-panel story/dialogue.

    If Gemini is unavailable or its quota is exhausted,
    automatically use the local fallback.
    """

    outline_json = json.dumps(
        outline,
        ensure_ascii=False,
    )

    prompt = f"""
Expand the following comic outline into a
panel-by-panel comic story.

MAIN CHARACTER:
{character_name}

TONE:
{tone}

OUTLINE:
{outline_json}

Create EXACTLY 5 story panels.

For EVERY panel generate:

panel_number
narration
dialogue
caption

Rules:

- Exactly 5 panels.
- Panel numbers must be 1, 2, 3, 4, 5.
- Maintain continuity.
- Keep the main character consistent.
- Keep the setting consistent.
- Narration must contain 1 to 3 concise sentences.
- Dialogue should sound natural.
- If dialogue is unnecessary, use an empty string.
- Caption should be short.
- Keep the story suitable for a general audience.
- Return ONLY valid JSON.

JSON format:

[
    {{
        "panel_number": 1,
        "narration": "...",
        "dialogue": "...",
        "caption": "..."
    }}
]
"""

    # ========================================================
    # TRY GEMINI ONCE
    # ========================================================
    #
    # IMPORTANT:
    # Do NOT retry several times when the daily quota is
    # exhausted. The API itself reports that the quota may
    # remain unavailable for many hours.
    # ========================================================

    try:

        print()
        print("=" * 60)
        print("STEP 2: GENERATING COMIC STORY")
        print("=" * 60)

        print(
            f"Gemini story generation using "
            f"{settings.gemini_pro_model}..."
        )

        client = get_client()

        response = client.models.generate_content(
            model=settings.gemini_pro_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[PanelStory],
                max_output_tokens=3000,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty story."
            )

        data = json.loads(
            response.text
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "Gemini story response is not a list."
            )

        stories = []

        for index, item in enumerate(
            data[:5],
            start=1,
        ):

            stories.append(
                PanelStory.model_validate(
                    {
                        "panel_number": index,
                        "narration": str(
                            item.get(
                                "narration",
                                "",
                            )
                        ),
                        "dialogue": str(
                            item.get(
                                "dialogue",
                                "",
                            )
                        ),
                        "caption": str(
                            item.get(
                                "caption",
                                "",
                            )
                        ),
                    }
                )
            )

        if len(stories) != 5:
            raise RuntimeError(
                "Gemini did not return exactly 5 story panels."
            )

        print(
            "Successfully generated 5 story panels."
        )

        return [
            story.model_dump()
            for story in stories
        ]

    # ========================================================
    # GEMINI FAILURE
    # ========================================================

    except Exception as exc:

        print()
        print("=" * 60)
        print("GEMINI STORY GENERATION FAILED")
        print("=" * 60)
        print(str(exc))
        print("=" * 60)

        if is_quota_error(exc):

            print(
                "Gemini API quota/rate limit detected."
            )

            print(
                "Gemini is unavailable right now."
            )

        else:

            print(
                "Gemini story generation failed."
            )

        # ====================================================
        # LOCAL FALLBACK
        # ====================================================

        print(
            "Using LOCAL 5-PANEL STORY FALLBACK."
        )

        fallback = create_fallback_story(
            outline=outline,
            character_name=character_name,
            tone=tone,
        )

        if len(fallback) != 5:
            raise RuntimeError(
                "Local story fallback failed to create "
                "exactly 5 panels."
            )

        print(
            "Successfully created 5-panel "
            "local story fallback."
        )

        return fallback
