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

from api.routes_coldpool import router as coldpool_router
from api.routes_econ_safe import router as econ_safe_router
from api.routes_landings import router as landings_router
from api.routes_oceanhealth import router as oceanhealth_router
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
        "Marine Heatwave State Dashboard — REST API for the sub-arctic to Arctic "
        "marine waters around Alaska (Gulf of Alaska, Bering Sea, Chukchi, Beaufort).\n\n"
        "Serves aggregated daily metrics, per-cell map payloads, climate indices, "
        "and event summaries. All data endpoints are versioned under `/v1`. The "
        "service-level `/health` endpoint is unversioned."
    ),
    version="1.0.0",
    root_path=os.getenv("API_ROOT_PATH", ""),
    swagger_ui_parameters={"url": "openapi.json"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — all data endpoints are mounted under /v1
# ---------------------------------------------------------------------------
app.include_router(states_router,   prefix="/v1", tags=["Regions"])
app.include_router(maps_router,     prefix="/v1", tags=["Maps"])
app.include_router(indices_router,  prefix="/v1", tags=["Indices"])
app.include_router(coldpool_router, prefix="/v1", tags=["Cold Pool"])
app.include_router(oceanhealth_router, prefix="/v1", tags=["Ocean Health"])
app.include_router(landings_router, prefix="/v1", tags=["Landings"])
app.include_router(econ_safe_router, prefix="/v1", tags=["Economic SAFE"])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Meta"])
def health():
    """Liveness check — always returns 200 OK."""
    return {"status": "ok", "version": app.version}
