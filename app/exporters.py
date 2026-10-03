# app/exporters.py

from pathlib import Path
from datetime import datetime
import re

from fpdf import FPDF

from app.config import settings


# ============================================================
# PDF-SAFE TEXT
# ============================================================

def pdf_safe_text(text):
    """
    Convert Unicode text into text that works with FPDF's
    built-in Helvetica font.

    FPDF built-in fonts use Latin-1 encoding, so characters
    such as bullets, em-dashes and smart quotes can cause
    FPDFUnicodeEncodingException.
    """

    if text is None:
        return ""

    text = str(text)

    replacements = {
        # Bullets
        "•": "-",
        "●": "*",
        "▪": "-",
        "◦": "-",

        # Dashes
        "–": "-",
        "—": "-",
        "-": "-",

        # Quotes
        "“": '"',
        "”": '"',
        "„": '"',
        "‘": "'",
        "’": "'",

        # Other common Unicode characters
        "…": "...",
        "→": "->",
        "←": "<-",
        "↔": "<->",

        # Check/cross
        "✓": "[OK]",
        "✔": "[OK]",
        "✗": "[X]",
        "✘": "[X]",

        # Non-breaking space
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Final protection against unsupported characters.
    return (
        text
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


# ============================================================
# FILENAME CLEANING
# ============================================================

def clean_filename(text):
    """
    Convert a title into a safe Windows filename.
    """

    text = pdf_safe_text(text)

    text = re.sub(
        r'[<>:"/\\|?*]',
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        "_",
        text.strip(),
    )

    text = text[:80]

    if not text:
        text = "comic"

    return text


# ============================================================
# IMAGE PATH RESOLUTION
# ============================================================

def resolve_image_path(image_url):
    """
    Convert a ComicCraft image URL/path into a local file path.
    """

    if not image_url:
        return None

    image_url = str(image_url)

    # --------------------------------------------------------
    # Already a local Windows path
    # --------------------------------------------------------

    possible_path = Path(image_url)

    if possible_path.exists():
        return possible_path


    # --------------------------------------------------------
    # /static/panels/panel_xxx.png
    # --------------------------------------------------------

    if image_url.startswith("/static/"):
        relative = image_url[len("/static/"):]

        local_path = (
            settings.output_dir / relative
        )

        if local_path.exists():
            return local_path


    # --------------------------------------------------------
    # static/panels/panel_xxx.png
    # --------------------------------------------------------

    if image_url.startswith("static/"):
        relative = image_url[len("static/"):]

        local_path = (
            settings.output_dir / relative
        )

        if local_path.exists():
            return local_path


    # --------------------------------------------------------
    # /panels/panel_xxx.png
    # --------------------------------------------------------

    if image_url.startswith("/panels/"):
        filename = Path(image_url).name

        local_path = (
            settings.panels_dir / filename
        )

        if local_path.exists():
            return local_path


    # --------------------------------------------------------
    # Just a filename
    # --------------------------------------------------------

    filename = Path(image_url).name

    local_path = (
        settings.panels_dir / filename
    )

    if local_path.exists():
        return local_path


    # --------------------------------------------------------
    # Absolute path that does not exist
    # --------------------------------------------------------

    return None


# ============================================================
# GET PANEL VALUE
# ============================================================

def get_panel_value(panel, *keys, default=""):
    """
    Safely retrieve the first available value from a panel.
    """

    if panel is None:
        return default

    if isinstance(panel, dict):

        for key in keys:

            value = panel.get(key)

            if value is not None:
                return value

    return default


# ============================================================
# NORMALIZE LAYOUT
# ============================================================

def normalize_layout(layout):
    """
    Convert different possible layout structures into a
    simple list of panel dictionaries.
    """

    if layout is None:
        return []

    # --------------------------------------------------------
    # Layout is already a list
    # --------------------------------------------------------

    if isinstance(layout, list):
        return layout


    # --------------------------------------------------------
    # Layout is a dictionary containing panels
    # --------------------------------------------------------

    if isinstance(layout, dict):

        panels = layout.get("panels")

        if isinstance(panels, list):
            return panels

        # Some builders may use "pages"
        pages = layout.get("pages")

        if isinstance(pages, list):
            return pages

        # Single panel dictionary
        if "panel_number" in layout:
            return [layout]

    return []


# ============================================================
# COMIC PDF CLASS
# ============================================================

class ComicPDF(FPDF):

    def header(self):
        # ComicCraft intentionally does not add a header
        # automatically to every page.
        pass

    def footer(self):
        self.set_y(-12)

        self.set_font(
            "Helvetica",
            "",
            7,
        )

        self.set_text_color(
            120,
            120,
            120,
        )

        self.cell(
            0,
            5,
            pdf_safe_text(
                f"ComicCraft - Page {self.page_no()}"
            ),
            align="C",
        )

        self.set_text_color(
            0,
            0,
            0,
        )


# ============================================================
# ADD COVER PAGE
# ============================================================

def add_cover_page(pdf, title):
    """
    Add a simple ComicCraft cover page.
    """

    pdf.add_page()

    pdf.set_font(
        "Helvetica",
        "B",
        24,
    )

    pdf.set_text_color(
        25,
        25,
        25,
    )

    pdf.ln(45)

    pdf.multi_cell(
        0,
        14,
        pdf_safe_text(title),
        align="C",
    )

    pdf.ln(10)

    pdf.set_font(
        "Helvetica",
        "",
        12,
    )

    pdf.set_text_color(
        90,
        90,
        90,
    )

    pdf.cell(
        0,
        8,
        "Generated with ComicCraft",
        align="C",
    )

    pdf.ln(12)

    pdf.set_font(
        "Helvetica",
        "",
        9,
    )

    pdf.cell(
        0,
        6,
        datetime.now().strftime(
            "%d %B %Y"
        ),
        align="C",
    )

    pdf.set_text_color(
        0,
        0,
        0,
    )


# ============================================================
# ADD PANEL
# ============================================================

def add_panel_page(
    pdf,
    panel,
    panel_index,
):
    """
    Add one comic panel to the PDF.
    """

    panel_number = get_panel_value(
        panel,
        "panel_number",
        "number",
        default=panel_index,
    )

    title = get_panel_value(
        panel,
        "title",
        "panel_title",
        default=f"Panel {panel_number}",
    )

    scene_description = get_panel_value(
        panel,
        "scene_description",
        "description",
        "scene",
        default="",
    )

    dialogue = get_panel_value(
        panel,
        "dialogue",
        "dialog",
        "text",
        "caption",
        default="",
    )

    image_url = get_panel_value(
        panel,
        "image_url",
        "image",
        "image_path",
        "url",
        default="",
    )


    # --------------------------------------------------------
    # PAGE
    # --------------------------------------------------------

    pdf.add_page()


    # --------------------------------------------------------
    # PANEL TITLE
    # --------------------------------------------------------

    pdf.set_font(
        "Helvetica",
        "B",
        15,
    )

    pdf.set_text_color(
        20,
        20,
        20,
    )

    safe_title = pdf_safe_text(
        f"Panel {panel_number} - {title}"
    )

    pdf.cell(
        0,
        10,
        safe_title,
        ln=True,
    )

    pdf.ln(2)


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    image_path = resolve_image_path(
        image_url
    )

    if image_path:

        print()
        print(
            f"Panel {panel_number} image URL: "
            f"{image_url}"
        )

        print(
            f"Local image path: "
            f"{image_path}"
        )

        try:

            from PIL import Image

            with Image.open(image_path) as img:
                width, height = img.size

            print(
                f"Image size: "
                f"{width}x{height}"
            )

        except Exception:

            width = 1024
            height = 1024


        # ----------------------------------------------------
        # A4 page
        # ----------------------------------------------------

        page_width = pdf.w

        page_height = pdf.h

        margin = 32.5

        available_width = (
            page_width - (margin * 2)
        )

        max_image_height = 145


        # Keep aspect ratio
        if width > 0 and height > 0:

            image_height = (
                available_width
                * height
                / width
            )

        else:

            image_height = max_image_height


        image_height = min(
            image_height,
            max_image_height,
        )


        x = margin

        y = 38


        print(
            f"Adding image to PDF: "
            f"{image_path}"
        )

        print(
            f"PDF image position: "
            f"x={x:.2f}, "
            f"y={y:.2f}, "
            f"w={available_width:.2f}, "
            f"h={image_height:.2f}"
        )


        try:

            pdf.image(
                str(image_path),
                x=x,
                y=y,
                w=available_width,
                h=image_height,
            )

            print(
                "Image added successfully."
            )

        except Exception as exc:

            print(
                f"WARNING: Could not add image: "
                f"{exc}"
            )

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            pdf.set_text_color(
                150,
                0,
                0,
            )

            pdf.multi_cell(
                0,
                6,
                pdf_safe_text(
                    f"Image could not be loaded: "
                    f"{image_path}"
                ),
            )

            pdf.set_text_color(
                0,
                0,
                0,
            )

    else:

        print(
            f"WARNING: Image not found for "
            f"panel {panel_number}: "
            f"{image_url}"
        )

        pdf.set_font(
            "Helvetica",
            "I",
            10,
        )

        pdf.cell(
            0,
            10,
            "Panel image unavailable.",
            ln=True,
        )


    # --------------------------------------------------------
    # TEXT POSITION
    # --------------------------------------------------------

    pdf.set_y(195)


    # --------------------------------------------------------
    # SCENE DESCRIPTION
    # --------------------------------------------------------

    if scene_description:

        pdf.set_font(
            "Helvetica",
            "B",
            10,
        )

        pdf.cell(
            0,
            7,
            "Scene",
            ln=True,
        )

        pdf.set_font(
            "Helvetica",
            "",
            9,
        )

        pdf.multi_cell(
            0,
            5,
            pdf_safe_text(
                scene_description
            ),
        )

        pdf.ln(4)


    # --------------------------------------------------------
    # DIALOGUE / CAPTION
    # --------------------------------------------------------

    if dialogue:

        pdf.set_font(
            "Helvetica",
            "B",
            10,
        )

        pdf.cell(
            0,
            7,
            "Dialogue",
            ln=True,
        )

        pdf.set_font(
            "Helvetica",
            "",
            9,
        )

        pdf.multi_cell(
            0,
            5,
            pdf_safe_text(
                dialogue
            ),
        )


# ============================================================
# SAVE PDF
# ============================================================

def save_pdf(
    layout,
    title,
):
    """
    Export the generated comic as a PDF.

    Parameters
    ----------
    layout:
        Comic layout returned by build_comic_layout().

    title:
        Comic title.

    Returns
    -------
    str
        Browser-accessible PDF URL.
    """

    print()
    print("=" * 60)
    print("EXPORTING COMIC PDF")
    print("=" * 60)


    # --------------------------------------------------------
    # Ensure directories exist
    # --------------------------------------------------------

    settings.ensure_directories()


    # --------------------------------------------------------
    # Normalize layout
    # --------------------------------------------------------

    panels = normalize_layout(
        layout
    )

    if not panels:

        raise RuntimeError(
            "Cannot export PDF: comic layout "
            "contains no panels."
        )


    # --------------------------------------------------------
    # Create safe filename
    # --------------------------------------------------------

    safe_title = clean_filename(
        title
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{safe_title}_{timestamp}.pdf"
    )


    output = (
        settings.exports_dir
        / filename
    )


    print(
        f"PDF output path: {output}"
    )


    # --------------------------------------------------------
    # Create PDF
    # --------------------------------------------------------

    pdf = ComicPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )


    # Margins
    pdf.set_margins(
        left=15,
        top=15,
        right=15,
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )


    # --------------------------------------------------------
    # COVER
    # --------------------------------------------------------

    add_cover_page(
        pdf,
        title,
    )


    # --------------------------------------------------------
    # PANELS
    # --------------------------------------------------------

    for index, panel in enumerate(
        panels,
        start=1,
    ):

        print()
        print(
            f"Exporting panel "
            f"{index}/{len(panels)}..."
        )

        add_panel_page(
            pdf,
            panel,
            index,
        )


    # --------------------------------------------------------
    # WRITE PDF
    # --------------------------------------------------------

    try:

        pdf.output(
            str(output)
        )

    except Exception as exc:

        raise RuntimeError(
            f"PDF export failed: {exc}"
        ) from exc


    # --------------------------------------------------------
    # VERIFY FILE
    # --------------------------------------------------------

    if not output.exists():

        raise RuntimeError(
            "PDF export completed but the "
            "PDF file was not created."
        )


    file_size = output.stat().st_size


    if file_size <= 0:

        raise RuntimeError(
            "PDF file was created but is empty."
        )


    print()
    print(
        f"PDF successfully created: "
        f"{output}"
    )

    print(
        f"PDF size: "
        f"{file_size:,} bytes"
    )


    # --------------------------------------------------------
    # Browser URL
    # --------------------------------------------------------

    pdf_url = (
        "/static/exports/"
        + filename
    )


    print(
        f"PDF URL: {pdf_url}"
    )

    print("=" * 60)
    print("PDF EXPORT COMPLETE")
    print("=" * 60)


    return pdf_url