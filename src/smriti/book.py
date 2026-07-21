"""
PDF memoir book generator.
Produces a formatted PDF from a grandparent's seven-story chapter sprint.
"""

import html
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from .config import config
from .db import Family, Grandparent, Story, get_family_stories, open_session
from .prompts import PROMPTS_ENGLISH, PROMPTS_HINDI

logger = logging.getLogger(__name__)


def _download_noto_font() -> Optional[str]:
    """Download Noto Sans to /tmp if not already cached. Returns path or None."""
    import urllib.request
    font_dir = Path("/tmp/smriti_fonts")
    font_dir.mkdir(exist_ok=True)
    font_path = font_dir / "NotoSans-Regular.ttf"
    if font_path.exists():
        return str(font_path)
    url = (
        "https://github.com/notofonts/noto-fonts/raw/main/"
        "hinted/ttf/NotoSans/NotoSans-Regular.ttf"
    )
    try:
        urllib.request.urlretrieve(url, font_path)
        logger.info("PDF font: downloaded Noto Sans to %s", font_path)
        return str(font_path)
    except Exception as exc:
        logger.warning("PDF font: could not download Noto Sans: %s", exc)
        return None


def _register_unicode_font() -> str:
    """
    Register a TTF font with Devanagari support for ReportLab.
    Tries local system fonts first, then downloads Noto Sans to /tmp.
    Returns the registered font name.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = []
    if platform.system() == "Darwin":
        candidates += ["/Library/Fonts/Arial Unicode.ttf"]
    candidates += [
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/noto/NotoSans-Regular.ttf",
        str(Path(__file__).parent / "fonts" / "NotoSans-Regular.ttf"),
    ]
    # On Vercel / cloud Linux: download to /tmp
    downloaded = _download_noto_font()
    if downloaded:
        candidates.append(downloaded)

    for path in candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont("SmritiUnicode", path))
                logger.info("PDF font: registered %s", path)
                return "SmritiUnicode"
            except Exception as exc:
                logger.warning("PDF font: could not register %s: %s", path, exc)

    logger.warning("PDF font: no Unicode font found — Devanagari will not render.")
    return "Helvetica"


_BODY_FONT = _register_unicode_font()


def _styles():
    base = getSampleStyleSheet()
    body = _BODY_FONT
    body_bold = "Helvetica-Bold" if body == "Helvetica" else body

    title_style = ParagraphStyle(
        "SmritiTitle",
        parent=base["Title"],
        fontSize=28,
        textColor=colors.HexColor("#2C1810"),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "SmritiSubtitle",
        parent=base["Normal"],
        fontSize=14,
        textColor=colors.HexColor("#6B4226"),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName=body,
    )
    chapter_style = ParagraphStyle(
        "SmritiChapter",
        parent=base["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#2C1810"),
        spaceBefore=20,
        spaceAfter=8,
        fontName=body_bold,
    )
    prompt_style = ParagraphStyle(
        "SmritiPrompt",
        parent=base["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#6B4226"),
        spaceAfter=10,
        fontName=body,
        leftIndent=20,
        rightIndent=20,
    )
    story_style = ParagraphStyle(
        "SmritiStory",
        parent=base["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=16,
        leading=18,
        alignment=TA_JUSTIFY,
        fontName=body,
    )
    week_label = ParagraphStyle(
        "SmritiWeek",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#999999"),
        spaceAfter=4,
        fontName="Helvetica",
    )
    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "chapter": chapter_style,
        "prompt": prompt_style,
        "story": story_style,
        "week": week_label,
    }


def _chapter_title(index: int) -> str:
    chapters = [
        (0, 9, "Childhood"),
        (10, 19, "Youth"),
        (20, 29, "Family"),
        (30, 39, "Work & World"),
        (40, 47, "Wisdom"),
        (48, 51, "Legacy"),
    ]
    for start, end, name in chapters:
        if start <= index <= end:
            return name
    return "Stories"


def generate_book(family_id: int, output_path: Optional[str] = None) -> str:
    """
    Generate a PDF memoir book for a family.
    Returns the path to the generated PDF.
    """
    output_dir = Path(config.books_dir)
    output_dir.mkdir(exist_ok=True)

    with open_session() as session:
        family = session.get(Family, family_id)
        if not family:
            raise ValueError(f"Family {family_id} not found")

    pairs = get_family_stories(family_id)
    if not pairs:
        raise ValueError(f"No grandparents found for family {family_id}")

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"smriti-{family.grandchild_name.lower().replace(' ', '-')}-{timestamp}.pdf"
        output_path = str(output_dir / filename)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=3 * cm,
        leftMargin=3 * cm,
        topMargin=3 * cm,
        bottomMargin=3 * cm,
    )

    styles = _styles()
    story_elements = []

    story_elements.append(Spacer(1, 4 * cm))
    story_elements.append(Paragraph("smriti", styles["title"]))
    story_elements.append(Spacer(1, 0.5 * cm))

    names = " &amp; ".join(gp.name for gp, _ in pairs)
    story_elements.append(Paragraph(f"The Life and Stories of {names}", styles["subtitle"]))
    story_elements.append(Spacer(1, 1 * cm))
    story_elements.append(
        Paragraph(f"A gift from {family.grandchild_name}", styles["subtitle"])
    )
    story_elements.append(Spacer(1, 0.5 * cm))
    year = datetime.now().year
    story_elements.append(Paragraph(str(year), styles["subtitle"]))
    story_elements.append(PageBreak())

    story_elements.append(Paragraph("A Note", styles["chapter"]))
    story_elements.append(
        Paragraph(
            f"This book was made with love. Over seven days, {names} answered one question "
            f"each day — about their childhood, their family, the world they grew up in, and "
            f"the wisdom they have carried through life. These are their words, their memories, "
            f"and their stories. They belong to this family, now and always.",
            styles["story"],
        )
    )
    story_elements.append(PageBreak())

    current_chapter = None
    for gp, stories in pairs:
        if len(pairs) > 1:
            story_elements.append(Paragraph(gp.name, styles["title"]))
            story_elements.append(PageBreak())

        for story in stories:
            chapter = _chapter_title(story.prompt_index)
            if chapter != current_chapter:
                current_chapter = chapter
                story_elements.append(Paragraph(chapter, styles["chapter"]))
                story_elements.append(
                    HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D4A96A"))
                )
                story_elements.append(Spacer(1, 0.3 * cm))

            story_elements.append(
                Paragraph(f"Day {story.prompt_index + 1}", styles["week"])
            )
            story_elements.append(
                Paragraph(f"<i>{html.escape(story.prompt_text)}</i>", styles["prompt"])
            )
            story_elements.append(Spacer(1, 0.2 * cm))

            body_text = story.enhanced_text or story.reply_text
            if body_text:
                story_elements.append(Paragraph(html.escape(body_text), styles["story"]))
            else:
                story_elements.append(
                    Paragraph("<i>(No response recorded)</i>", styles["prompt"])
                )
            story_elements.append(Spacer(1, 0.4 * cm))

    story_elements.append(PageBreak())
    story_elements.append(Spacer(1, 8 * cm))
    story_elements.append(Paragraph("smriti", styles["title"]))
    story_elements.append(
        Paragraph("स्मृति — memory, that which is worth keeping.", styles["subtitle"])
    )

    doc.build(story_elements)
    logger.info("Book generated: %s", output_path)
    # On Vercel /tmp is ephemeral — upload to object storage and hand back a
    # signed URL when configured; otherwise the local path is returned unchanged.
    from .storage import store_pdf
    return store_pdf(output_path)
