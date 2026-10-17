"""Stage the board's heatwave record (vintage #7, D1) into a read-only folder the nightly never writes.

Copies the release files the board reads — region aggregates, coverage sidecars and the 540 annual
state stores — from the sealed release into ``data/record/mhw-d1/`` (or ``MHW_RECORD_DIR``), checking
every file's sha256 against the release manifest *before and after* the copy. Then:

* copies m4's frozen 2016 SEBS panel table (daily CSV + overlap CSV), verified against m4's checksum
  lists and the folder's top-level SHA256SUMS (b7b25fbe…);
* recomputes the coverage-aware risk percentiles from the staged files into ``risk/`` (board-derived,
  not a release file; the vintage-#6 risk folder is left untouched);
* writes ``RECORD.json`` (identity) and ``RECORD_SHA256SUMS`` (``sha256sum -c`` format, every staged
  file) so the deployed copy can be verified on the server.

The sealed release is opened read-only and never written. Refuses to stage into a non-empty folder
unless ``--replace`` is given.

CLI:
    python scripts/stage_d1_record.py [--release DIR] [--panel DIR] [--dest DIR] [--replace]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mhw import record  # noqa: E402

DEFAULT_RELEASE = PROJECT_ROOT / "data" / "derived" / "releases" / record.RECORD_ID
DEFAULT_PANEL = (Path.home() / "dev" / "acfr" / "projects" / "mhw-areafrac-properties" / "validation"
                 / "ice-gap-resolution" / "m4-2016-sebs-panel-table-20261012")
MANIFEST_SHA256 = "329c0d1bd57a418c1a2a7f15774b4ff965ddcb7621133e47d7549b8fa8869714"
PANEL_SUMS_SHA256 = "b7b25fbe9e6243965cda7b5b779224cfba98b073d08806b08f850aad6d380c4a"
PANEL_FILES = ("sebs_2016_panel_daily.csv", "sebs_2016_panel_history_overlap.csv")

# release payload prefix → staged subfolder
STAGE_MAP = {
    "native/aggregates_region/": "aggregates_region/",
    "products/coverage_daily/": "coverage_daily/",
    "native/states_grid/": "states_grid/",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(release: Path) -> dict[str, tuple[int, str]]:
    """relpath (under payload/) → (bytes, sha256); refuses a manifest that is not the sealed one."""
    mpath = release / "records" / "MANIFEST.tsv"
    got = sha256(mpath)
    if got != MANIFEST_SHA256:
        raise SystemExit(f"REFUSE: {mpath} sha256 {got} != sealed {MANIFEST_SHA256}")
    out: dict[str, tuple[int, str]] = {}
    lines = mpath.read_text().splitlines()
    if lines[0].split("\t") != ["relpath", "bytes", "sha256"]:
        raise SystemExit(f"REFUSE: unexpected manifest header {lines[0]!r}")
    for line in lines[1:]:
        rel, n, h = line.split("\t")
        out[rel] = (int(n), h)
    return out


def select(manifest: dict[str, tuple[int, str]]) -> list[tuple[str, str]]:
    """(release relpath, staged relpath) for every file the board reads."""
    pairs = []
    for rel in sorted(manifest):
        for src_prefix, dst_prefix in STAGE_MAP.items():
            if rel.startswith(src_prefix):
                pairs.append((rel, dst_prefix + rel[len(src_prefix):]))
    return pairs


def verify_panel(panel: Path) -> dict[str, str]:
    """Verify m4's frozen panel folder; return {file name: sha256} for the two panel CSVs."""
    top = panel / "SHA256SUMS"
    if sha256(top) != PANEL_SUMS_SHA256:
        raise SystemExit(f"REFUSE: {top} is not the frozen list {PANEL_SUMS_SHA256[:8]}…")
    listed: dict[str, str] = {}
    for line in top.read_text().splitlines():
        h, rel = line.split(maxsplit=1)
        listed[rel.strip()] = h
    att = panel / "out" / "attempt-01"
    for lst in ("SHA256SUMS", "SHA256SUMS.addendum"):
        rel = f"out/attempt-01/{lst}"
        if sha256(att / lst) != listed[rel]:
            raise SystemExit(f"REFUSE: {rel} does not match the top-level list")
        for line in (att / lst).read_text().splitlines():
            h, name = line.split(maxsplit=1)
            listed[f"out/attempt-01/{name.strip()}"] = h
    out = {}
    for name in PANEL_FILES:
        want = listed[f"out/attempt-01/{name}"]
        got = sha256(att / name)
        if got != want:
            raise SystemExit(f"REFUSE: panel file {name} sha256 {got} != listed {want}")
        out[name] = got
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    p.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    p.add_argument("--dest", type=Path, default=None, help="default: mhw.record.record_dir()")
    p.add_argument("--replace", action="store_true", help="clear a non-empty destination first")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dest = args.dest or record.record_dir()
    payload = args.release / "payload"

    if dest.exists() and any(dest.iterdir()):
        if not args.replace:
            raise SystemExit(f"REFUSE: {dest} is not empty (use --replace)")
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    manifest = read_manifest(args.release)
    pairs = select(manifest)
    print(f"Staging {len(pairs):,} release files → {dest}")
    sums: list[tuple[str, str]] = []
    for i, (rel, staged) in enumerate(pairs, 1):
        n, want = manifest[rel]
        src = payload / rel
        if src.stat().st_size != n or sha256(src) != want:
            raise SystemExit(f"REFUSE: release file {rel} does not match the manifest")
        out = dest / staged
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, out)
        if sha256(out) != want:
            raise SystemExit(f"FAIL: staged copy {staged} differs from the manifest")
        sums.append((want, staged))
        if i % 10000 == 0:
            print(f"  {i:,} / {len(pairs):,}")

    panel = verify_panel(args.panel)
    (dest / "panel2016").mkdir()
    for name, h in panel.items():
        shutil.copyfile(args.panel / "out" / "attempt-01" / name, dest / "panel2016" / name)
        if sha256(dest / "panel2016" / name) != h:
            raise SystemExit(f"FAIL: staged panel file {name} differs")
        sums.append((h, f"panel2016/{name}"))
    print(f"Panel: {len(panel)} files verified against m4's frozen lists ({PANEL_SUMS_SHA256[:8]}…)")

    # Board-derived: coverage-aware risk percentiles from the staged files.
    import os
    os.environ["MHW_RECORD_DIR"] = str(dest)
    from mhw.states.risk import main as risk_main
    for zone in sorted(record.list_zones()):
        if risk_main(["--region", zone, "--record"]) != 0:
            raise SystemExit(f"FAIL: risk recompute for {zone}")
    for p in sorted((dest / "risk").glob("risk_*.parquet")):
        sums.append((sha256(p), f"risk/{p.name}"))

    ident = {
        "record_id": record.RECORD_ID,
        "vintage": record.VINTAGE_LABEL,
        "seal_prefix": record.SEAL_PREFIX,
        "manifest_sha256": MANIFEST_SHA256,
        "certified_through": record.CERTIFIED_THROUGH.isoformat(),
        "panel2016_source_sums_sha256": PANEL_SUMS_SHA256,
        "staged_release_files": len(pairs),
        "board_derived": ["risk/"],
        "staged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (dest / "RECORD.json").write_text(json.dumps(ident, indent=1) + "\n")
    sums.append((sha256(dest / "RECORD.json"), "RECORD.json"))
    (dest / "RECORD_SHA256SUMS").write_text("".join(f"{h}  {p}\n" for h, p in sums))
    print(f"Wrote RECORD.json and RECORD_SHA256SUMS ({len(sums):,} files). "
          f"sha256(RECORD_SHA256SUMS) = {sha256(dest / 'RECORD_SHA256SUMS')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
