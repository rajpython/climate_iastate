"""MHW State API — FastAPI entry point.

Run:
    uvicorn src.api.main:app --reload
    uvicorn src.api.main:app --reload --port 8000

Docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_indices import router as indices_router
from api.routes_maps import router as maps_router
from api.routes_states import router as states_router

ROOT = Path(__file__).parents[2]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: print data paths. Shutdown: nothing to clean up."""
    agg_dir = ROOT / "data" / "derived" / "aggregates_region"
    parquets = list(agg_dir.glob("region_daily_*.parquet"))
    print(f"[MHW API] aggregates found: {[p.name for p in parquets]}")
    zarr_dir = ROOT / "data" / "derived" / "states_grid"
    zarrs = list(zarr_dir.glob("*.zarr")) if zarr_dir.exists() else []
    print(f"[MHW API] state zarrs found: {len(zarrs)}")
    yield


app = FastAPI(
    title="MHW State API",
    description=(
        "Marine Heatwave State Dashboard — REST API for GOA and adjacent regions.\n\n"
        "Serves aggregated daily metrics, per-cell map payloads, climate indices, "
        "event summaries, and risk scores."
    ),
    version="0.1.0",
    root_path=os.getenv("API_ROOT_PATH", ""),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(states_router,  tags=["States"])
app.include_router(maps_router,    tags=["Maps"])
app.include_router(indices_router, tags=["Indices"])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Meta"])
def health():
    """Liveness check — always returns 200 OK."""
    return {"status": "ok", "version": app.version}
