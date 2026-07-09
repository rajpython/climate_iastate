"""PowerPoint export — turn a chat's charts/findings into a downloadable ``.pptx`` deck.

Server-side and frontend-agnostic: returns a token; the API serves the file by token. Charts are
Plotly figure dicts (from :mod:`charts`) rasterised to PNG via kaleido — **pinned kaleido 0.2.1**
because 1.x needs a system Chrome the slim image lacks (0.2.x bundles its own). Each content slide is
a blue heading + a large chart on the left + interpretation bullets on the right; the chart's own
title is dropped (the slide heading is the title) so the plot gets full vertical room.
"""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

REPORTS_DIR = Path(
    os.getenv("ASSISTANT_REPORTS_DIR", str(Path(tempfile.gettempdir()) / "mhw_assistant_reports"))
)

_HEADING_RGB = (0x16, 0x40, 0x7A)   # NOAA-style blue, matches the dashboard
_BODY_RGB = (0x33, 0x41, 0x4F)      # dark slate
_SUB_RGB = (0x5F, 0x6B, 0x7A)


def report_path(token: str) -> Path | None:
    """Resolve a download token to a file path (None if unknown/absent). Token is a bare filename."""
    if not token or "/" in token or "\\" in token or ".." in token:
        return None
    p = REPORTS_DIR / token
    return p if p.exists() else None


def _fig_png(fig_dict: dict) -> bytes:
    import plotly.graph_objects as go
    import plotly.io as pio

    fig = go.Figure(fig_dict)
    # The slide heading is the title — drop the chart's own title and reclaim the top space.
    fig.update_layout(title_text="", margin={"t": 28})
    return pio.to_image(fig, format="png", width=1120, height=680, scale=2)


def build_report(
    title: str,
    slides: list[dict[str, Any]],
    subtitle: str = "",
    out_dir: Path | None = None,
) -> dict:
    """Build a deck and return ``{"token", "filename"}``.

    ``slides`` is a list of ``{"heading", "bullets": [str], "chart": <plotly dict|None>}``.
    """
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    out_dir = Path(out_dir) if out_dir else REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    s0 = prs.slides.add_slide(prs.slide_layouts[0])
    s0.shapes.title.text = title or "Alaska Marine Ecosystems — Data Report"
    if s0.placeholders and len(s0.placeholders) > 1:
        s0.placeholders[1].text = subtitle or "Generated from marine.iastate.ai"

    blank = prs.slide_layouts[6]
    for slide in slides:
        s = prs.slides.add_slide(blank)

        # Heading (blue, bold) + a thin accent rule beneath it.
        head = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
        htf = head.text_frame
        htf.word_wrap = True
        htf.text = str(slide.get("heading", ""))
        hp = htf.paragraphs[0]
        hp.font.size = Pt(26)
        hp.font.bold = True
        hp.font.color.rgb = RGBColor(*_HEADING_RGB)

        chart = slide.get("chart")
        bullets = slide.get("bullets") or []

        if chart:
            img_path = out_dir / f"_img_{uuid.uuid4().hex}.png"
            img_path.write_bytes(_fig_png(chart))
            s.shapes.add_picture(str(img_path), Inches(0.45), Inches(1.35), width=Inches(8.5))
            img_path.unlink(missing_ok=True)
            box = s.shapes.add_textbox(Inches(9.25), Inches(1.45), Inches(3.65), Inches(5.6))
            body_pt, sub = 14, False
        else:
            box = s.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.4))
            body_pt, sub = 18, False

        btf = box.text_frame
        btf.word_wrap = True
        for i, b in enumerate(bullets):
            p = btf.paragraphs[0] if i == 0 else btf.add_paragraph()
            p.text = f"•  {b}"
            p.font.size = Pt(body_pt)
            p.font.color.rgb = RGBColor(*(_SUB_RGB if sub else _BODY_RGB))
            p.space_after = Pt(9)
            p.line_spacing = 1.08

    token = f"{uuid.uuid4().hex}.pptx"
    prs.save(str(out_dir / token))
    safe_name = (title or "report").strip().replace(" ", "_")[:60] or "report"
    return {"token": token, "filename": f"{safe_name}.pptx"}
