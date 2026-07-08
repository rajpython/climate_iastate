"""PowerPoint export — turn a chat's charts/findings into a downloadable ``.pptx`` deck.

Server-side and frontend-agnostic: returns a token; the API serves the file by token. Charts are
Plotly figure dicts (from :mod:`charts`) rasterised to PNG via kaleido — **pinned kaleido 0.2.1**
because 1.x needs a system Chrome the slim image lacks (0.2.x bundles its own).
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


def report_path(token: str) -> Path | None:
    """Resolve a download token to a file path (None if unknown/absent). Token is a bare filename."""
    if not token or "/" in token or "\\" in token or ".." in token:
        return None
    p = REPORTS_DIR / token
    return p if p.exists() else None


def _fig_png(fig_dict: dict) -> bytes:
    import plotly.graph_objects as go
    import plotly.io as pio

    return pio.to_image(go.Figure(fig_dict), format="png", width=900, height=520, scale=2)


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
        # Heading
        head = s.shapes.add_textbox(Inches(0.5), Inches(0.35), Inches(12.3), Inches(0.9))
        tf = head.text_frame
        tf.text = str(slide.get("heading", ""))
        tf.paragraphs[0].font.size = Pt(28)
        tf.paragraphs[0].font.bold = True

        chart = slide.get("chart")
        bullets = slide.get("bullets") or []

        if chart:
            img = _fig_png(chart)
            img_path = out_dir / f"_img_{uuid.uuid4().hex}.png"
            img_path.write_bytes(img)
            s.shapes.add_picture(str(img_path), Inches(0.5), Inches(1.4),
                                 width=Inches(8.2))
            img_path.unlink(missing_ok=True)
            box = s.shapes.add_textbox(Inches(9.0), Inches(1.4), Inches(3.9), Inches(5.5))
        else:
            box = s.shapes.add_textbox(Inches(0.6), Inches(1.5), Inches(12.0), Inches(5.3))

        btf = box.text_frame
        btf.word_wrap = True
        for i, b in enumerate(bullets):
            p = btf.paragraphs[0] if i == 0 else btf.add_paragraph()
            p.text = f"• {b}"
            p.font.size = Pt(16)

    token = f"{uuid.uuid4().hex}.pptx"
    (out_dir / token).parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_dir / token))
    safe_name = (title or "report").strip().replace(" ", "_")[:60] or "report"
    return {"token": token, "filename": f"{safe_name}.pptx"}
