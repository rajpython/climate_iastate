"""Drive the running Streamlit dashboard with Playwright and capture screenshots.

Reusable visual-check tool for this project. Assumes the dashboard is already
running (``streamlit run src/dashboard/MHW_Dashboard.py``) on --port (default 8501).

Usage:
    # start the app first (headless), then:
    .venv/bin/python scripts/screenshot_dashboard.py --page Bottom_Cold_Pool \
        --select "Bering10K ROMS" "CEFI MOM6 NEP" --out /tmp/dash.png

Requires: pip install playwright && playwright install chromium
"""
from __future__ import annotations

import argparse
import sys
import time

from playwright.sync_api import sync_playwright


def main() -> int:
    ap = argparse.ArgumentParser(description="Screenshot a Streamlit dashboard page.")
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--page", default="", help="Streamlit page slug (e.g. Bottom_Cold_Pool); blank = home")
    ap.add_argument("--select", nargs="*", default=[], help="Multiselect option labels to choose")
    ap.add_argument("--region", default="", help="Region selectbox value to choose (e.g. SLOPE)")
    ap.add_argument("--out", default="/tmp/dashboard.png")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--height", type=int, default=1000)
    args = ap.parse_args()

    url = f"http://localhost:{args.port}/{args.page}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(2500)  # let Streamlit hydrate

        if args.region:
            # The region picker is the first selectbox in the sidebar.
            sb = page.locator('[data-testid="stSelectbox"]').first
            sb.click()
            page.wait_for_timeout(400)
            try:
                page.keyboard.type(args.region, delay=25)
                page.wait_for_timeout(600)
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)  # let the page re-render for the new region
            except Exception as e:  # noqa: BLE001
                print(f"  ! could not select region {args.region!r}: {e}", file=sys.stderr)

        if args.select:
            # Target the Streamlit multiselect specifically (not other selectboxes).
            ms = page.locator('[data-testid="stMultiSelect"]').first
            ms.click()
            page.wait_for_timeout(400)
            for label in args.select:
                try:
                    page.keyboard.type(label, delay=25)
                    page.wait_for_timeout(600)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(800)
                except Exception as e:  # noqa: BLE001
                    print(f"  ! could not select {label!r}: {e}", file=sys.stderr)
            page.keyboard.press("Escape")

        page.wait_for_timeout(2500)  # let plotly charts render
        page.screenshot(path=args.out, full_page=True)
        browser.close()
    print(f"saved → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
