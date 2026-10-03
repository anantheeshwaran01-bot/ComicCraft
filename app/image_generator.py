from pathlib import Path
from uuid import uuid4
import base64

import requests
from PIL import Image, ImageDraw

from app.config import settings


def create_filename(index: int) -> str:
    return f"panel_{index}_{uuid4().hex[:8]}.png"


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

    draw.rectangle(
        (25, 25, 999, 743),
        outline="black",
        width=5,
    )

    draw.text(
        (55, 55),
        f"ComicCraft - Panel {index}",
        fill="black",
    )

    draw.multiline_text(
        (55, 130),
        prompt[:500],
        fill="black",
        spacing=8,
    )

    image.save(output, format="PNG")


def generate_cloudflare_image(
    prompt: str,
    output: Path,
) -> None:

    account_id = settings.cloudflare_account_id
    token = settings.cloudflare_api_token
    model = settings.cloudflare_image_model

    url = (
        f"https://api.cloudflare.com/client/v4/"
        f"accounts/{account_id}/ai/run/{model}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        headers=headers,
        json={
            "prompt": prompt,
        },
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("success"):
        raise RuntimeError(
            f"Cloudflare API failed: {data}"
        )

    image_data = data.get("result", {}).get("image")

    if not image_data:
        raise RuntimeError(
            "Cloudflare returned no image data."
        )

    # Cloudflare returns base64 image data
    image_bytes = base64.b64decode(image_data)

    with open(output, "wb") as f:
        f.write(image_bytes)


def generate_image(
    prompt: str,
    index: int,
) -> str:

    settings.ensure_directories()

    filename = create_filename(index)
    output = settings.panels_dir / filename

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

        generate_cloudflare_image(
            enhanced_prompt,
            output,
        )

        # Verify the generated file
        with Image.open(output) as im:
            im.verify()

        # Check actual image
        with Image.open(output) as im:
            print(
                f"Image {index} generated successfully."
            )
            print(
                f"Image size: {im.size}"
            )

        print(f"Saved to: {output}")

        return f"/static/panels/{filename}"

    except Exception as e:

        print("=" * 60)
        print(
            f"Cloudflare image generation failed "
            f"for panel {index}"
        )
        print(f"ERROR: {e}")
        print("Creating local fallback image...")
        print("=" * 60)

        create_placeholder(
            prompt,
            output,
            index,
        )

        return f"/static/panels/{filename}"