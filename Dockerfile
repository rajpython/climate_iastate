FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System libraries needed by netcdf4, h5py, and geo packages.
# Shapely 2.x / rasterio / cartopy ship manylinux wheels so only
# HDF5 + NetCDF C libs are strictly required at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gcc \
        g++ \
        libhdf5-dev \
        libnetcdf-dev \
        libgeos-dev \
        libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python deps (own layer — rebuilt only when pyproject.toml changes) ───────
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install -e ".[geo,dashboard,api]"

# ── Config files baked into image (not data — that is bind-mounted) ──────────
COPY config/ ./config/
COPY docs/ ./docs/
COPY .streamlit/ ./.streamlit/

# ── Runtime directories (populated by bind-mount or manual copy) ─────────────
RUN mkdir -p data/raw data/derived outputs

EXPOSE 8000 8501
