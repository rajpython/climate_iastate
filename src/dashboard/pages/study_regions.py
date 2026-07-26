"""Study Regions — the 12 Alaska-shelf ecosystem zones that drive the whole board, with a
single annotated map and cited provenance for every boundary.

A path-registered page (runs top-to-bottom, like ``literature.py``). It renders the committed
region-boundary map (``docs/region_boundaries.png``) and reads the sealed provenance sidecar
(``config/regions_provenance.json``) at runtime, so the zone list and citations never drift from
the geometry the masks/aggregation/forecasts are built on. Page config / fonts are owned by the
navigation shell.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
MAP_PNG = ROOT / "docs" / "region_boundaries.png"
PROVENANCE_JSON = ROOT / "config" / "regions_provenance.json"

# Ecosystem grouping (matches the board's geography-first sections). Leaves in map order.
GROUPS = [
    ("Bering Sea", ["sebs", "nbs"], "ebs"),
    ("Gulf of Alaska", ["wgoa", "egoa"], "goa"),
    ("Aleutian Islands", ["ai_west", "ai_central", "ai_east"], "ai"),
    ("Arctic", ["chukchi", "beaufort"], None),
]

_CSS = """<style>
.sr-title { font-size:2.1rem; font-weight:800; color:#16407a; line-height:1.15; margin:0; }
.sr-lead { font-size:1.0rem; color:#33414f; margin:0.4rem 0 0.2rem; max-width:82ch; }
.sr-sec { font-size:0.82rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;
    color:#1565c0; margin:0.2rem 0 0.5rem; }
.sr-group { font-size:1.15rem; font-weight:700; color:#16407a; margin:0 0 0.1rem; }
.sr-rollup { font-size:0.8rem; color:#5f6b7a; margin:0 0 0.6rem; }
.sr-zone { font-size:1.0rem; font-weight:700; color:#2b3a4a; margin:0.55rem 0 0.1rem; }
.sr-bnd { font-size:0.9rem; line-height:1.45; color:#2b3a4a; margin:0.05rem 0; }
.sr-bnd b { color:#16407a; }
.sr-quote { font-size:0.85rem; line-height:1.4; color:#455160; border-left:3px solid #c9d6e5;
    padding:0.05rem 0 0.05rem 0.6rem; margin:0.15rem 0 0.15rem 0.2rem; font-style:italic; }
.sr-note { font-size:0.83rem; line-height:1.4; color:#8a5a00; background:#fff6e5;
    border-left:3px solid #e0a800; padding:0.25rem 0.6rem; margin:0.2rem 0 0.2rem 0.2rem;
    border-radius:0 4px 4px 0; }
.sr-doctrine { font-size:0.95rem; line-height:1.5; color:#22303c; }
.sr-src { font-size:0.86rem; line-height:1.45; color:#2b3a4a; margin:0.2rem 0; }
.sr-src b { color:#16407a; }
.sr-footer { font-size:0.8rem; color:#7a8694; }
</style>"""


@st.cache_resource
def _load_provenance() -> dict:
    return json.loads(PROVENANCE_JSON.read_text(encoding="utf-8"))


def _render_boundary(b: dict) -> None:
    """One provenance row: boundary → value, optional verbatim quote, optional open-item note."""
    st.markdown(
        f"<div class='sr-bnd'>· <b>{b['boundary']}</b> — {b['value']}</div>",
        unsafe_allow_html=True,
    )
    if b.get("quote"):
        st.markdown(f"<div class='sr-quote'>“{b['quote']}”</div>", unsafe_allow_html=True)
    if b.get("note"):
        st.markdown(f"<div class='sr-note'>⚠ {b['note']}</div>", unsafe_allow_html=True)


# --- Header -------------------------------------------------------------------------------
st.markdown(_CSS, unsafe_allow_html=True)
st.markdown("<div class='sr-title'>🗺️ Study Regions</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sr-lead'>The board reports on <b>12 Alaska-shelf ecosystem zones</b> — nine "
    "leaf zones plus three roll-ups (Eastern Bering Sea, Gulf of Alaska, Aleutian Islands). "
    "One shared set of polygons (<code>config/regions.geojson</code>) drives every mask, "
    "aggregation, map, and forecast on the platform. This page shows where those zones are and "
    "cites the primary NOAA source for every boundary.</div>",
    unsafe_allow_html=True,
)
st.divider()

try:
    prov = _load_provenance()
except FileNotFoundError:
    st.error(f"Provenance sidecar not found: {PROVENANCE_JSON}")
    st.stop()
feats = prov["features"]
sources = prov["sources"]

# --- The map ------------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='sr-sec'>The zones on one map</div>", unsafe_allow_html=True)
    if MAP_PNG.exists():
        st.image(str(MAP_PNG), use_container_width=True)
    else:
        st.warning(
            "Region-boundary map not found. Generate it with "
            "`.venv/bin/python scripts/plot_region_boundaries.py` (needs the `[geo]` extra)."
        )
    st.caption(
        "Nine ESR leaf zones. Outer edges follow the coast/shelf; internal divides (red) are the "
        "AFSC/ESR management meridians and parallels detailed below."
    )

# --- Doctrine -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='sr-sec'>Which boundary reference is authoritative</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='sr-doctrine'>This is an <b>ecosystem</b> board, so the authoritative "
        "reference is the <b>AFSC Ecosystem Status Report (ESR) ecoregions</b> — physics- and "
        "biogeography-driven boundaries (oceanographic passes, fronts, water-mass breaks) — "
        "<b>not</b> the NMFS fishery-management statistical/survey areas (e.g. Aleutian districts "
        "541/542/543). The two zonations overlap and <i>disagree by design</i>. The canonical "
        "case is the Aleutians: the ESR splits Central↔Eastern at <b>Samalga Pass ≈ 170°W</b> (a "
        "first-order biogeographic break), while management splits at 177°W. The board follows the "
        "ESR.</div>",
        unsafe_allow_html=True,
    )

# --- Per-zone provenance, grouped by ecosystem --------------------------------------------
st.markdown("<div class='sr-sec' style='margin-top:0.6rem;'>Zone-by-zone provenance</div>",
            unsafe_allow_html=True)
for group_name, leaves, rollup in GROUPS:
    with st.container(border=True):
        st.markdown(f"<div class='sr-group'>{group_name}</div>", unsafe_allow_html=True)
        if rollup and rollup in feats:
            members = ", ".join(feats[m]["name"] for m in feats[rollup]["members"])
            st.markdown(
                f"<div class='sr-rollup'>Roll-up <b>{feats[rollup]['name']}</b> = {members}.</div>",
                unsafe_allow_html=True,
            )
        for leaf in leaves:
            f = feats[leaf]
            st.markdown(
                f"<div class='sr-zone'>{f['name']} "
                f"<span style='font-weight:400;color:#7a8694;'>({leaf})</span></div>",
                unsafe_allow_html=True,
            )
            for b in f.get("provenance", []):
                _render_boundary(b)

# --- Sources ------------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='sr-sec'>Cited sources</div>", unsafe_allow_html=True)
    for key, s in sources.items():
        url = s.get("url", "")
        ref = s.get("ref", key)
        locator = s.get("locator", "")
        link = f" &nbsp;<a href='{url}' target='_blank'>source ↗</a>" if url else ""
        loc = f" &nbsp;·&nbsp; <i>{locator}</i>" if locator else ""
        st.markdown(f"<div class='sr-src'><b>{key}</b> — {ref}{loc}{link}</div>",
                    unsafe_allow_html=True)

st.divider()
st.markdown(
    "<div class='sr-footer'>Boundaries are sealed in <code>config/regions.geojson</code>; "
    "machine-checkable values live in <code>config/regions_provenance.json</code> and are enforced "
    "by <code>tests/test_region_provenance.py</code> (any drift fails CI). Full narrative: "
    "<code>docs/region_provenance.md</code> and <code>docs/arctic_region_provenance.md</code>.</div>",
    unsafe_allow_html=True,
)
