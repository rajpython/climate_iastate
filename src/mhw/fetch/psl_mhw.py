"""NOAA PSL experimental Marine Heatwave forecast — conditional NetCDF fetcher.

Source
------
NOAA PSL marine-heatwave downloads (Jacox et al. 2022 NMME MHW probability):
    https://downloads.psl.noaa.gov/Datasets/marinehw/
File set, window and header schema live in config/psl_mhw.yml. PSL refreshes
the ``*_latest.nc`` files ~monthly (sometimes mid-month as models land), so
this fetcher is designed to run **daily from cron**: it HEADs each file,
compares Last-Modified/length against a local ``<file>.meta.json`` sidecar,
and downloads only what changed. On quiet days it transfers no data.

Exit codes (for the cron script to branch on):
    0 — at least one file was downloaded (rebuild derived artifacts)
    3 — everything unchanged (skip the rebuild)

CLI: mhw-fetch-psl-mhw [--force] [--include-hindcast]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

# ---------------------------------------------------------------------------
# Project paths / config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "psl_mhw.yml"

_TIMEOUT = 60  # seconds; the forecast files are a few hundred MB
EXIT_UNCHANGED = 3


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Conditional-download logic (pure part is unit-testable)
# ---------------------------------------------------------------------------

def need_download(remote: dict, local: dict) -> bool:
    """Decide whether the remote file differs from what we last downloaded.

    Pure (no network / no filesystem). ``remote``/``local`` are metadata dicts
    with optional keys ``last_modified`` (str) and ``length`` (int). Prefers
    Last-Modified when both sides have it, falls back to content length, and
    downloads when there is nothing to compare (fail open — a spurious
    re-download is cheap; a stale forecast is not).
    """
    if not local:
        return True
    r_lm, l_lm = remote.get("last_modified"), local.get("last_modified")
    r_len, l_len = remote.get("length"), local.get("length")
    if r_lm and l_lm:
        if r_lm != l_lm:
            return True
        return r_len is not None and l_len is not None and r_len != l_len
    if r_len is not None and l_len is not None:
        return r_len != l_len
    return True


def _sidecar_path(dest: Path) -> Path:
    return dest.with_name(dest.name + ".meta.json")


def _local_meta(dest: Path) -> dict:
    """Metadata recorded at last successful download; {} if file or sidecar missing."""
    if not dest.exists():
        return {}
    try:
        return json.loads(_sidecar_path(dest).read_text())
    except (OSError, ValueError):
        return {}


def _remote_meta(url: str) -> dict:
    resp = requests.head(url, timeout=_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    length = resp.headers.get("Content-Length")
    return {
        "last_modified": resp.headers.get("Last-Modified"),
        "length": int(length) if length is not None else None,
        "etag": resp.headers.get("ETag"),
    }


def download_file(url: str, dest: Path, remote: dict | None = None) -> None:
    """Streamed download to ``<dest>.part`` then atomic replace, plus sidecar.

    The atomic replace means a killed download can never leave a truncated
    ``*_latest.nc`` where the build step would read it.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with requests.get(url, timeout=_TIMEOUT, stream=True) as resp:
        resp.raise_for_status()
        with open(part, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    os.replace(part, dest)
    meta = dict(remote or {})
    meta["length"] = dest.stat().st_size
    meta["fetched_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _sidecar_path(dest).write_text(json.dumps(meta, indent=2))


def fetch_file_set(files: dict[str, str], base_url: str, raw_dir: Path,
                   force: bool = False) -> dict[str, list[str]]:
    """HEAD each file, download the changed ones. Returns {"updated": [...], "unchanged": [...]}."""
    result: dict[str, list[str]] = {"updated": [], "unchanged": []}
    for key, fname in files.items():
        url = base_url + fname
        dest = raw_dir / fname
        remote = _remote_meta(url)
        if not force and not need_download(remote, _local_meta(dest)):
            print(f"  {fname}: unchanged")
            result["unchanged"].append(fname)
            continue
        size_note = f" ({remote['length'] / 1e6:,.0f} MB)" if remote.get("length") else ""
        print(f"  {fname}: downloading{size_note} …")
        download_file(url, dest, remote)
        print(f"    Saved → {dest}")
        result["updated"].append(fname)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Conditionally fetch NOAA PSL marine-heatwave forecast NetCDF files.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Download everything regardless of the Last-Modified check",
    )
    parser.add_argument(
        "--include-hindcast", action="store_true",
        help="Also fetch the static 1991-2020 hindcast files (~1.1 GB each; "
             "needed only for the local SEDI skill build — never from cron)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    cfg = load_config()

    base_url = cfg["source"]["base_url"]
    raw_dir = PROJECT_ROOT / cfg["source"]["raw_dir"]

    files = dict(cfg["source"]["latest_files"])
    files.update(cfg["source"]["static_files"])
    if args.include_hindcast:
        files.update(cfg["source"]["hindcast_files"])

    print(f"Fetching PSL marine-heatwave files from {base_url} …")
    result = fetch_file_set(files, base_url, raw_dir, force=args.force)

    if result["updated"]:
        print(f"\nPSL_MHW: updated {','.join(result['updated'])}")
    else:
        print("\nPSL_MHW: unchanged")
        sys.exit(EXIT_UNCHANGED)


if __name__ == "__main__":
    main()
