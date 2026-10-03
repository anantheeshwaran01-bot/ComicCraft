from pathlib import Path
from uuid import uuid4
import base64
import random
import time

import requests
from PIL import Image, ImageDraw, ImageFont

from app.config import settings


# ============================================================
# FILE NAME
# ============================================================

def create_filename(index: int) -> str:
    return f"panel_{index}_{uuid4().hex[:8]}.png"


# ============================================================
# FALLBACK IMAGE
# ============================================================

def create_placeholder(
    prompt: str,
    output: Path,
    index: int,
) -> None:

    image = Image.new(
        "RGB",
        (1024, 768),
        "white",
    )

    draw = ImageDraw.Draw(image)

    # Border
    draw.rectangle(
        (20, 20, 1004, 748),
        outline="black",
        width=6,
    )

    # Header
    draw.text(
        (50, 45),
        f"ComicCraft - Panel {index}",
        fill="black",
    )

    # Separator
    draw.line(
        (50, 95, 974, 95),
        fill="black",
        width=2,
    )

    # Message
    draw.text(
        (50, 125),
        "AI image generation temporarily unavailable.",
        fill="black",
    )

    draw.text(
        (50, 165),
        "Please try again later.",
        fill="black",
    )

    # Prompt
    draw.multiline_text(
        (50, 240),
        prompt[:800],
        fill="black",
        spacing=10,
    )

    image.save(
        output,
        format="PNG",
    )


# ============================================================
# CLOUDFLARE IMAGE GENERATION
# ============================================================

def generate_cloudflare_image(
    prompt: str,
    output: Path,
) -> None:

    account_id = settings.cloudflare_account_id
    token = settings.cloudflare_api_token
    model = settings.cloudflare_image_model

    if not account_id:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID is not configured."
        )

    if not token:
        raise RuntimeError(
            "CLOUDFLARE_API_TOKEN is not configured."
        )

    url = (
        "https://api.cloudflare.com/client/v4/"
        f"accounts/{account_id}/ai/run/{model}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Maximum number of attempts
    max_attempts = 4

    for attempt in range(1, max_attempts + 1):

        print(
            f"Cloudflare request "
            f"(attempt {attempt}/{max_attempts})"
        )

        try:

            response = requests.post(
                url,
                headers=headers,
                json={
                    "prompt": prompt,
                },
                timeout=180,
            )

            # ------------------------------------------------
            # RATE LIMIT / CAPACITY
            # ------------------------------------------------

            if response.status_code == 429:

                print(
                    "Cloudflare returned HTTP 429 "
                    "(rate limit / capacity / quota)."
                )

                if attempt == max_attempts:
                    raise RuntimeError(
                        "Cloudflare returned HTTP 429 "
                        "after all retry attempts. "
                        "Check your Workers AI usage/quota."
                    )

                # Respect Retry-After when provided
                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:
                        wait_time = float(retry_after)
                    except ValueError:
                        wait_time = 2 ** attempt

                else:
                    wait_time = (
                        (2 ** attempt)
                        + random.uniform(0, 1)
                    )

                print(
                    f"Waiting {wait_time:.1f} seconds "
                    "before retry..."
                )

                time.sleep(wait_time)

                continue

            # ------------------------------------------------
            # TEMPORARY SERVER ERRORS
            # ------------------------------------------------

            if response.status_code in (500, 502, 503, 504):

                print(
                    f"Cloudflare returned "
                    f"HTTP {response.status_code}."
                )

                if attempt == max_attempts:
                    response.raise_for_status()

                wait_time = (
                    (2 ** attempt)
                    + random.uniform(0, 1)
                )

                print(
                    f"Waiting {wait_time:.1f} seconds "
                    "before retry..."
                )

                time.sleep(wait_time)

                continue

            # ------------------------------------------------
            # OTHER HTTP ERRORS
            # ------------------------------------------------

            response.raise_for_status()

            # ------------------------------------------------
            # JSON RESPONSE
            # ------------------------------------------------

            data = response.json()

            if not data.get("success"):

                raise RuntimeError(
                    f"Cloudflare API failed: {data}"
                )

            result = data.get("result") or {}

            image_data = result.get("image")

            if not image_data:

                raise RuntimeError(
                    f"Cloudflare returned no image data: "
                    f"{data}"
                )

            # ------------------------------------------------
            # BASE64 IMAGE
            # ------------------------------------------------

            try:

                image_bytes = base64.b64decode(
                    image_data
                )

            except Exception as e:

                raise RuntimeError(
                    "Failed to decode Cloudflare "
                    "base64 image data."
                ) from e

            # Save image
            with open(output, "wb") as f:
                f.write(image_bytes)

            print(
                "Cloudflare image downloaded successfully."
            )

            return

        except requests.Timeout as e:

            print(
                f"Cloudflare request timed out: {e}"
            )

            if attempt == max_attempts:
                raise RuntimeError(
                    "Cloudflare request timed out "
                    "after all retry attempts."
                ) from e

            wait_time = (
                (2 ** attempt)
                + random.uniform(0, 1)
            )

            print(
                f"Retrying in {wait_time:.1f} seconds..."
            )

            time.sleep(wait_time)

        except requests.RequestException as e:

            print(
                f"Cloudflare request error: {e}"
            )

            if attempt == max_attempts:
                raise

            wait_time = (
                (2 ** attempt)
                + random.uniform(0, 1)
            )

            print(
                f"Retrying in {wait_time:.1f} seconds..."
            )

            time.sleep(wait_time)


# ============================================================
# IMAGE GENERATION
# ============================================================

def generate_image(
    prompt: str,
    index: int,
) -> str:

    settings.ensure_directories()

    filename = create_filename(index)

    output = settings.panels_dir / filename

    # --------------------------------------------------------
    # ENHANCED PROMPT
    # --------------------------------------------------------

    enhanced_prompt = (
        "Create a high quality anime comic book panel. "
        "Clean professional illustration, detailed characters, "
        "cinematic composition, dramatic lighting, "
        "consistent character appearance. "
        "No text, no speech bubbles, no captions, "
        "no watermark. "
        + prompt
    )

    print("=" * 60)

    print(
        f"Generating image {index} using Cloudflare: "
        f"{settings.cloudflare_image_model}"
    )

    print("=" * 60)

    try:

        # ----------------------------------------------------
        # GENERATE
        # ----------------------------------------------------

        generate_cloudflare_image(
            enhanced_prompt,
            output,
        )

        # ----------------------------------------------------
        # VERIFY IMAGE
        # ----------------------------------------------------

        with Image.open(output) as im:

            im.verify()

        with Image.open(output) as im:

            print(
                f"Image {index} generated successfully."
            )

            print(
                f"Image size: {im.size}"
            )

        print(
            f"Saved to: {output}"
        )

        return (
            f"/static/panels/{filename}"
        )

    except Exception as e:

        print("=" * 60)

        print(
            f"Cloudflare image generation failed "
            f"for panel {index}"
        )

        print(
            f"ERROR: {e}"
        )

        print(
            "Creating local fallback image."
        )

        print("=" * 60)

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        create_placeholder(
            prompt,
            output,
            index,
        )

        return (
            f"/static/panels/{filename}"
        )