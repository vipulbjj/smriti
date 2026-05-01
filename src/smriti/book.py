"""
PDF memoir book generator.
Produces a formatted PDF from a grandparent's 52 stories.
"""

import html
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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

from .db import Family, Grandparent, Story, get_family_stories, open_session
from .prompts import PROMPTS_ENGLISH, PROMPTS_HINDI

OUTPUT_DIR = Path("books")


def _styles():
    base = getSampleStyleSheet()

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
        fontName="Helvetica",
    )
    chapter_style = ParagraphStyle(
        "SmritiChapter",
        parent=base["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#2C1810"),
        spaceBefore=20,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    prompt_style = ParagraphStyle(
        "SmritiPrompt",
        parent=base["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#6B4226"),
        spaceAfter=10,
        fontName="Helvetica-Oblique",
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
        fontName="Helvetica",
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
    OUTPUT_DIR.mkdir(exist_ok=True)

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
        output_path = str(OUTPUT_DIR / filename)

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
    story_elements.append(Paragraph("🪔", styles["title"]))
    story_elements.append(Spacer(1, 0.5 * cm))
    story_elements.append(Paragraph("smriti", styles["title"]))
    story_elements.append(Spacer(1, 0.5 * cm))

    # Grandparent names
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

    # Foreword
    story_elements.append(Paragraph("A Note", styles["chapter"]))
    story_elements.append(
        Paragraph(
            f"This book was made with love. Over the past year, {names} answered one question "
            f"each week — about their childhood, their family, the world they grew up in, and "
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
                Paragraph(f"Week {story.prompt_index + 1}", styles["week"])
            )
            story_elements.append(
                Paragraph(f"<i>{story.prompt_text}</i>", styles["prompt"])
            )
            story_elements.append(Spacer(1, 0.2 * cm))

            if story.reply_text:
                story_elements.append(Paragraph(html.escape(story.reply_text), styles["story"]))
            else:
                story_elements.append(
                    Paragraph("<i>(No response recorded)</i>", styles["prompt"])
                )
            story_elements.append(Spacer(1, 0.4 * cm))

    # Back page
    story_elements.append(PageBreak())
    story_elements.append(Spacer(1, 8 * cm))
    story_elements.append(Paragraph("🪔 smriti", styles["title"]))
    story_elements.append(
        Paragraph("स्मृति — memory, that which is worth keeping.", styles["subtitle"])
    )

    doc.build(story_elements)
    return output_path
