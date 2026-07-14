"""Climate Driver Links — standalone cross-zone page.

A sibling of the Marine Heatwaves hub under "Alaska-wide Climate". Hosts the single all-zones
driver × metric association matrix (moved off the per-region Climate Drivers tab, which now links
here). Body + chrome live in ``dashboard.components.driver_links``; this module just renders it.
"""
from __future__ import annotations

from dashboard.components.driver_links import render

render()
