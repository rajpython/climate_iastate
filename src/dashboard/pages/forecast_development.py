"""Forecast Development — methodology and progress on marine-heatwave forecasting.

A path-registered page (runs top-to-bottom, like ``cold_pool_position.py``). Forecasting is a
**separate research-cell programme**, not a board deliverable: forecast products are shown on the
dashboard only once they are publication-grade and validated. This page documents the programme's
framing, anchored by the forecasting synthesis (also listed under Literature Summaries). Page
config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
CONFIG_PATH = ROOT / "config" / "forecast.yml"
FORECAST_DIR = ROOT / "data" / "derived" / "forecast"
SYNTHESIS_PDF = "mhw_forecasting_synthesis.pdf"

# Full names for the zone tiles (short codes are keyed to the sealed 9-leaf partition).
_ZONE_NAMES = {
    "sebs": "Southeastern Bering", "nbs": "Northern Bering",
    "wgoa": "Western Gulf of Alaska", "egoa": "Eastern Gulf of Alaska",
    "ai_west": "W. Aleutians", "ai_central": "C. Aleutians", "ai_east": "E. Aleutians",
    "chukchi": "Chukchi", "beaufort": "Beaufort",
}
_CONFIDENCE_LABEL = {"headline": "headline", "banded": "banded", "watch": "low-confidence watch"}

BLUE, AMBER, SLATE = "#1565c0", "#b35900", "#5f6b7a"

_CSS = """<style>
.fc-title { font-size:2.1rem; font-weight:800; color:#16407a; line-height:1.15; margin:0; }
.fc-lead { font-size:1.0rem; color:#33414f; margin:0.4rem 0 0.2rem; max-width:82ch; }
.fc-sec { font-size:0.82rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;
    color:#1565c0; margin:0.2rem 0 0.5rem; }
.fc-card-title { font-size:1.1rem; font-weight:700; color:#16407a; margin:0 0 0.15rem; }
.fc-meta { font-size:0.8rem; color:#5f6b7a; margin-bottom:0.5rem; }
.fc-body { font-size:0.96rem; line-height:1.5; color:#2b3a4a; }
.fc-body li { margin-bottom:0.25rem; }
.fc-status { display:flex; gap:0.7rem; align-items:flex-start; border-radius:0.6rem;
    padding:0.75rem 1rem; border:1px solid #b3590055; background:#b359000d; }
.fc-status-txt { font-size:0.93rem; color:#2b3a4a; }
.fc-footer { font-size:0.8rem; color:#7a8694; }
.fc-tilegrid { display:grid; grid-template-columns:repeat(auto-fill, minmax(210px, 1fr));
    gap:0.7rem; margin:0.3rem 0 0.2rem; }
.fc-tile { border:1px solid #d3dbe4; border-radius:0.55rem; padding:0.7rem 0.85rem;
    background:#fbfcfe; }
.fc-tile-name { font-size:0.98rem; font-weight:700; color:#16407a; }
.fc-tile-role { font-size:0.72rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;
    color:#5f6b7a; margin-bottom:0.4rem; }
.fc-ladder { display:flex; flex-direction:column; gap:0.15rem; }
.fc-rung { display:flex; justify-content:space-between; font-size:0.85rem; color:#2b3a4a; }
.fc-rung .lv { color:#7a8694; }
.fc-chip { display:inline-block; font-size:0.72rem; font-weight:700; padding:0.08rem 0.5rem;
    border-radius:1rem; }
.fc-chip-clim { background:#eef1f5; color:#5f6b7a; }
.fc-chip-watch { background:#b359001a; color:#8a4600; border:1px solid #b3590044; }
.fc-caveat { font-size:0.76rem; color:#8a4600; margin-top:0.4rem; }
</style>"""


def _pdf_bytes(name: str) -> bytes | None:
    path = DOCS / name
    return path.read_bytes() if path.exists() else None


st.markdown(_CSS, unsafe_allow_html=True)

st.markdown("<div class='fc-title'>🧭 Forecast Development</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='fc-lead'>Methodology and progress on the forecasting of marine heatwaves and "
    "ocean thermal state for the Alaska shelf. Forecasting is pursued as a separate research "
    "programme; forecast products appear on the dashboard only once they are validated and "
    "scientifically defensible.</div>",
    unsafe_allow_html=True,
)

# --- Status banner ------------------------------------------------------------------------
st.markdown(
    "<div class='fc-status'><div style='font-size:1.4rem;color:#b35900;'>🚧</div>"
    "<div class='fc-status-txt'><b>Status — in development, not yet on the board.</b> This "
    "platform surfaces observed and modelled ecosystem state. A forecast layer is under "
    "development by the research programme and is held to a publication-grade evaluation gate "
    "(out-of-sample probabilistic skill against persistence and climatology, with explicit trend "
    "treatment) before any product is displayed.</div></div>",
    unsafe_allow_html=True,
)
st.divider()

# --- Forecast Outlook (scaffolded; provisional until the module lands) --------------------

def _load_forecast_config() -> dict | None:
    return yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else None


def _load_forecast(zone: str) -> pd.DataFrame | None:
    p = FORECAST_DIR / f"forecast_{zone}.parquet"
    return pd.read_parquet(p) if p.exists() else None


def _persistence_tile(zone: str, meta: dict, leads: list[dict]) -> str:
    name = _ZONE_NAMES.get(zone, zone.upper())
    df = _load_forecast(zone)
    rungs = []
    for lead in leads:
        conf = _CONFIDENCE_LABEL.get(lead.get("confidence", ""), lead.get("confidence", ""))
        val = "—"
        if df is not None and "lead" in df.columns:
            row = df[df["lead"] == lead["id"]]
            if not row.empty and pd.notna(row.iloc[0].get("point")):
                val = f"{float(row.iloc[0]['point']):.2f}"
        rungs.append(
            f"<div class='fc-rung'><span>{lead['id']} · {lead['months']} mo "
            f"<span class='lv'>({conf})</span></span><span>{val}</span></div>"
        )
    caveat = (
        "<div class='fc-caveat'>⚠︎ ice-contamination caveat · no LIM reading</div>"
        if meta.get("ice_caveat") else ""
    )
    return (
        f"<div class='fc-tile'><div class='fc-tile-name'>{name}</div>"
        f"<div class='fc-tile-role'>persistence · area_frac</div>"
        f"<div class='fc-ladder'>{''.join(rungs)}</div>{caveat}</div>"
    )


def _climatology_tile(zone: str) -> str:
    name = _ZONE_NAMES.get(zone, zone.upper())
    return (
        f"<div class='fc-tile'><div class='fc-tile-name'>{name}</div>"
        f"<div class='fc-tile-role'>climatology only</div>"
        f"<span class='fc-chip fc-chip-clim'>ice-affected</span>"
        f"<div class='fc-caveat'>Magnitude/area shown as climatology — a data limit, not skill.</div></div>"
    )


_cfg = _load_forecast_config()
if _cfg is not None:
    _leads = _cfg.get("leads", [])
    _zones = _cfg.get("zones", {})
    _vintage = _cfg.get("fit_vintage")
    _persist = [z for z, m in _zones.items() if m.get("role") == "persistence"]
    _clim = [z for z, m in _zones.items() if m.get("role") == "climatology"]
    _live = any((FORECAST_DIR / f"forecast_{z}.parquet").exists() for z in _persist)

    with st.container(border=True):
        st.markdown("<div class='fc-sec'>Forecast outlook</div>", unsafe_allow_html=True)
        state = ("Live" if _live else "Provisional — awaiting first module run")
        st.markdown(
            f"<div class='fc-meta'>Short-term MHW outlook · damped persistence on monthly "
            f"<code>area_frac</code> · <b>{state}</b></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='fc-body'>Division of labor is settled with the research cell: damped "
            "persistence at 1–3 month leads on an honesty ladder (L1 headline · L2 banded · L3 "
            "low-confidence watch), a Southeastern-Bering onset <b>watch</b> (elevated/normal — "
            "never a probability), and climatology only for the ice-affected Arctic zones. Tiles "
            "populate once the validated module is delivered and pinned.</div>",
            unsafe_allow_html=True,
        )
        tiles = [_persistence_tile(z, _zones[z], _leads) for z in _persist]
        tiles += [_climatology_tile(z) for z in _clim]
        # SEBS onset watch chip tile
        if _zones.get("sebs", {}).get("onset"):
            tiles.append(
                "<div class='fc-tile'><div class='fc-tile-name'>Southeastern Bering</div>"
                "<div class='fc-tile-role'>onset watch</div>"
                "<span class='fc-chip fc-chip-watch'>watch: awaiting data</span>"
                "<div class='fc-caveat'>Two-state discrimination indicator, not a probability/alarm.</div></div>"
            )
        st.markdown(f"<div class='fc-tilegrid'>{''.join(tiles)}</div>", unsafe_allow_html=True)
        vintage_txt = f"Fit vintage: <code>{_vintage}</code>" if _vintage else "Fit vintage: not yet pinned"
        st.markdown(f"<div class='fc-footer'>{vintage_txt} · frozen coefficients applied forward; "
                    "re-fits are research-cell re-validation events.</div>", unsafe_allow_html=True)


# --- Foundational synthesis ---------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='fc-sec'>Foundational synthesis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='fc-card-title'>Forecasting Marine Heatwaves in Alaska Shelf Seas: "
        "Methods, Predictability, and Validation Challenges</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='fc-meta'>Synthesis review · June 2026</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='fc-body'>The programme is scoped from a review of the forecasting literature "
        "for the Alaska shelf seas. Its conclusion frames the work: capable forecasting methods "
        "exist and the physical basis for predictability is reasonably well understood, but there "
        "is almost no <b>region-specific, validated, benchmarked</b> forecast evaluation for these "
        "shelves — so a defensible system must transfer a proven method in and prove its skill "
        "locally.</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1.1, 1.5])
    pdf = _pdf_bytes(SYNTHESIS_PDF)
    if pdf is not None:
        c1.download_button("Download PDF", data=pdf, file_name=SYNTHESIS_PDF,
                           mime="application/pdf", use_container_width=True)
    c2.page_link("pages/literature.py", label="Read the full summary in Literature →",
                 icon="📚", use_container_width=True)

# --- Where the science stands -------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='fc-sec'>Where the science stands</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='fc-body'><ul>"
        "<li><b>Methods are mature elsewhere.</b> Coupled dynamical seasonal systems, "
        "machine-learning and hybrid models, linear inverse models, and statistical baselines are "
        "established in open-ocean, temperate, and tropical systems.</li>"
        "<li><b>The Alaska shelf is a near-blank</b> for demonstrated forecast skill against a "
        "benchmark — the central gap the programme addresses.</li>"
        "<li><b>Predictability is dual.</b> Atmospheric teleconnection sequencing and subsurface "
        "ocean memory both contribute; the subsurface channel appears essential for the Gulf of "
        "Alaska.</li>"
        "<li><b>Distinct systems.</b> The Gulf of Alaska (surface SST) and the Bering/Arctic "
        "shelves (bottom thermal state, ice-conditioned) need different predictands and "
        "benchmarks.</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )

# --- Programme design ---------------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='fc-sec'>Evaluation design</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='fc-body'>The programme follows a structured evaluation rather than a single "
        "model:<ul>"
        "<li>Compare a <b>common method set</b> — climatology, persistence, damped persistence, "
        "autoregressive / vector-autoregressive models, linear inverse models, dynamical seasonal "
        "forecasts, and hybrid machine-learning corrections — over common hindcast periods.</li>"
        "<li>Use <b>identical event definitions</b> (fixed MHW threshold and baseline climatology) "
        "and <b>probabilistic verification</b> (Brier skill score and its decomposition, SEDI, "
        "ROC, reliability diagrams).</li>"
        "<li>Handle <b>trend explicitly</b>, reporting undetrended and detrended skill separately "
        "so secular warming is not mistaken for forecastable interannual skill.</li>"
        "<li>Evaluate the <b>Gulf of Alaska and the Bering/Chukchi/Beaufort shelves as separate "
        "systems</b>, each with predictands and benchmarks appropriate to it.</li>"
        "</ul>The deployment gate: a candidate must show superior out-of-sample probabilistic "
        "skill relative to persistence <i>and</i> climatology before any product is shown here.</div>",
        unsafe_allow_html=True,
    )

st.divider()
st.markdown(
    "<div class='fc-footer'>Forecast indicators, once validated, will appear alongside the "
    "relevant ecosystem indicators in the Alaska-wide and regional sections — not in this "
    "section, which documents the development and methodology.</div>",
    unsafe_allow_html=True,
)
