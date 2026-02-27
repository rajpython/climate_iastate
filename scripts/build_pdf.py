#!/usr/bin/env python3
"""Convert docs/user_guide.md to docs/user_guide.pdf.

Requirements:
    brew install pango          # system dependency
    pip install markdown weasyprint

Usage:
    python scripts/build_pdf.py
"""
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "user_guide.md"
PDF_PATH = ROOT / "docs" / "user_guide.pdf"

CSS = """
@page {
    size: letter;
    margin: 2.5cm 2cm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #888;
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #222;
}
h1 {
    font-size: 22pt;
    color: #1a5276;
    border-bottom: 2px solid #1a5276;
    padding-bottom: 6pt;
    margin-top: 30pt;
}
h2 {
    font-size: 16pt;
    color: #2c3e50;
    border-bottom: 1px solid #ddd;
    padding-bottom: 4pt;
    margin-top: 24pt;
}
h3 {
    font-size: 13pt;
    color: #2c3e50;
    margin-top: 18pt;
}
h4 {
    font-size: 11pt;
    color: #34495e;
    margin-top: 14pt;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
}
th, td {
    border: 1px solid #bbb;
    padding: 6pt 10pt;
    text-align: left;
}
th {
    background-color: #1a5276;
    color: white;
    font-weight: 600;
}
tr:nth-child(even) {
    background-color: #f2f6fa;
}
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 20pt 0;
}
a {
    color: #2980b9;
    text-decoration: none;
}
strong {
    font-weight: 700;
}
code {
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 10pt;
    background: #f4f4f4;
    padding: 1pt 4pt;
    border-radius: 3pt;
}
p {
    margin: 8pt 0;
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def main():
    md_text = MD_PATH.read_text(encoding="utf-8")

    # Convert markdown to HTML with table support
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "extra", "smarty"],
        output_format="html5",
    )

    full_html = HTML_TEMPLATE.format(css=CSS, body=html_body)

    HTML(string=full_html).write_pdf(str(PDF_PATH))
    size_kb = PDF_PATH.stat().st_size / 1024
    print(f"PDF generated: {PDF_PATH} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
