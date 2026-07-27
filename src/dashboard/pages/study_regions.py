"""Study Regions — the 12 Alaska-shelf ecosystem zones that drive the whole board, with a
single annotated map and the primary NOAA source cited for every boundary.

A path-registered page (runs top-to-bottom, like ``literature.py``). It renders the region map
(``docs/region_boundaries.png``) and reads the boundary sidecar (``config/regions_provenance.json``)
at runtime, so the zone list and citations never drift from the geometry the maps and indicators
are built on. All on-page text is plain-English and user-facing — the sidecar's ``label`` /
``boundary`` / ``value`` / ``note`` fields carry that wording; this page is a faithful renderer.
Page config / fonts are owned by the navigation shell.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
MAP_PNG = ROOT / "docs" / "region_boundaries.png"
PROVENANCE_JSON = ROOT / "config" / "regions_provenance.json"

# Ecosystem grouping (matches the board's geography-first sections). Zones in map order.
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
.sr-combined { font-size:0.85rem; color:#5f6b7a; margin:0 0 0.6rem; }
.sr-zone { font-size:1.0rem; font-weight:700; color:#2b3a4a; margin:0.55rem 0 0.1rem; }
.sr-bnd { font-size:0.92rem; line-height:1.45; color:#2b3a4a; margin:0.05rem 0; }
.sr-bnd b { color:#16407a; }
.sr-mark { color:#1565c0; font-weight:700; }
.sr-quote { font-size:0.85rem; line-height:1.4; color:#455160; border-left:3px solid #c9d6e5;
    padding:0.05rem 0 0.05rem 0.6rem; margin:0.15rem 0 0.15rem 0.2rem; font-style:italic; }
.sr-doctrine { font-size:0.95rem; line-height:1.5; color:#22303c; }
.sr-fn { font-size:0.9rem; line-height:1.45; color:#33414f; margin:0.15rem 0; }
.sr-fn b { color:#1565c0; }
.sr-src { font-size:0.9rem; line-height:1.4; color:#2b3a4a; margin:0.35rem 0; }
.sr-src b { color:#16407a; }
.sr-src-ref { font-size:0.83rem; color:#5f6b7a; margin-top:0.05rem; }
.sr-footer { font-size:0.82rem; line-height:1.45; color:#7a8694; }
</style>"""


@st.cache_resource
def _load_provenance() -> dict:
    return json.loads(PROVENANCE_JSON.read_text(encoding="utf-8"))


# --- Header -------------------------------------------------------------------------------
st.markdown(_CSS, unsafe_allow_html=True)
st.markdown("<div class='sr-title'>🗺️ Study Regions</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sr-lead'>The board reports on <b>12 Alaska-shelf ecosystem zones</b> — nine core "
    "zones plus three combined regions (the Eastern Bering Sea, the Gulf of Alaska, and the "
    "Aleutian Islands). One shared set of boundaries defines every map, indicator, and forecast on "
    "the platform. This page shows where the zones are and cites the primary NOAA source for each "
    "boundary.</div>",
    unsafe_allow_html=True,
)
st.divider()

try:
    prov = _load_provenance()
except FileNotFoundError:
    st.error("Region boundary reference not found.")
    st.stop()
feats = prov["features"]
sources = prov["sources"]

# --- The map ------------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='sr-sec'>The zones on one map</div>", unsafe_allow_html=True)
    if MAP_PNG.exists():
        st.image(str(MAP_PNG), use_container_width=True)
    else:
        st.warning("Region map is being prepared.")
    st.caption(
        "Nine core ecosystem zones. Outer edges follow the coast and shelf; the internal divides "
        "(red) are the NOAA ecosystem boundaries described below."
    )

# --- Which boundaries the board uses ------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='sr-sec'>Which boundaries the board uses</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='sr-doctrine'>This board describes <b>ecosystems</b>, so its boundaries come "
        "from NOAA's Alaska <b>Ecosystem Status Reports</b> — lines drawn where the ocean itself "
        "changes (passes, fronts, and water-mass boundaries). They are <b>not</b> the same as "
        "NOAA's fishery-management survey districts (for example, the Aleutian areas 541/542/543), "
        "which are drawn for setting catch limits. The two systems overlap but differ by design. "
        "The clearest example is the Aleutians: the ecosystem boundary between the Central and "
        "Eastern Aleutians falls at <b>Samalga Pass (about 170°W)</b> — a natural break in the "
        "marine environment — while the management boundary sits at 177°W. This board follows the "
        "ecosystem boundaries.</div>",
        unsafe_allow_html=True,
    )

# --- Per-zone boundaries, grouped by ecosystem (collecting footnotes) ---------------------
st.markdown("<div class='sr-sec' style='margin-top:0.6rem;'>Zone-by-zone boundaries</div>",
            unsafe_allow_html=True)
footnotes: list[str] = []
for group_name, leaves, rollup in GROUPS:
    with st.container(border=True):
        st.markdown(f"<div class='sr-group'>{group_name}</div>", unsafe_allow_html=True)
        if rollup and rollup in feats:
            members = ", ".join(feats[m]["name"] for m in feats[rollup]["members"])
            st.markdown(
                f"<div class='sr-combined'><b>{feats[rollup]['name']}</b> is a combined region: "
                f"{members}.</div>",
                unsafe_allow_html=True,
            )
        for leaf in leaves:
            f = feats[leaf]
            st.markdown(f"<div class='sr-zone'>{f['name']}</div>", unsafe_allow_html=True)
            for b in f.get("provenance", []):
                mark = ""
                if b.get("note"):
                    footnotes.append(b["note"])
                    mark = f" <span class='sr-mark'>[{len(footnotes)}]</span>"
                st.markdown(
                    f"<div class='sr-bnd'>· <b>{b['boundary']}:</b> {b['value']}{mark}</div>",
                    unsafe_allow_html=True,
                )
                if b.get("quote"):
                    st.markdown(f"<div class='sr-quote'>“{b['quote']}”</div>",
                                unsafe_allow_html=True)

# --- Footnotes (open items pulled out of the main flow) -----------------------------------
if footnotes:
    with st.container(border=True):
        st.markdown("<div class='sr-sec'>Notes</div>", unsafe_allow_html=True)
        for i, note in enumerate(footnotes, 1):
            st.markdown(f"<div class='sr-fn'><b>[{i}]</b> {note}</div>", unsafe_allow_html=True)

# --- Sources ------------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("<div class='sr-sec'>Cited sources</div>", unsafe_allow_html=True)
    for s in sources.values():
        label = s.get("label") or s.get("ref", "")
        ref = s.get("ref", "")
        locator = s.get("locator", "")
        url = s.get("url", "")
        link = f" &nbsp;<a href='{url}' target='_blank'>view source ↗</a>" if url else ""
        loc = f" &nbsp;·&nbsp; {locator}" if locator else ""
        st.markdown(
            f"<div class='sr-src'><b>{label}</b>"
            f"<div class='sr-src-ref'>{ref}{loc}{link}</div></div>",
            unsafe_allow_html=True,
        )

st.divider()
st.markdown(
    "<div class='sr-footer'>Every boundary shown here follows NOAA's Alaska Ecosystem Status "
    "Report ecoregions and is held fixed across the platform, so the map and the indicators built "
    "on it always agree. Each value is checked automatically against its cited source.</div>",
    unsafe_allow_html=True,
)
