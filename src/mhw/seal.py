"""Seal builder — package data for distribution with MEASURED, not hand-typed, gates.

Why this exists
---------------
The 2026-07-22 predictand seal shipped a ``vintage_manifest.json`` whose ``gates`` block
— including a ``"result": "PASS"`` — was hand-authored during the sealing session. One
gate asserted a property of the distributed arrays that was false for every holder (F2,
``PROGRAM-REGISTRY.md``): it described the producer's working tree while reading as a
machine verdict about the shipped bundle. The remedy this module implements, recorded in
``dashboard-to-admin-…-20260811-01`` §2: *the next seal is produced by a script — it
emits the manifest, computes each gate from artifacts it actually opens, reads the
as-shipped bytes back out of the packed archive, and writes the measured scope into
every gate note.* Until sealing was code, this repo shipped no gate blocks at all.

Design rules (each traceable to a defect in the F2 thread)
----------------------------------------------------------
1. **Gates live in a sidecar** (``<name>.gates.json``), never inside the archive. A gate
   about the archive's own bytes cannot live inside the bytes it measures; resolving
   that chicken-and-egg by hand is exactly how a PASS got typed.
2. **Verification reads the packed archive**, not the staging tree. Every gate re-reads
   members out of the tarball it will ship as.
3. **Every gate names its measured scope** (the ratified gate-scope rule: a verdict may
   not assert beyond what was read).
4. **The outer ``.sha256`` is written last, only if every gate passes.** No checksum
   file, no seal — a failed verify leaves nothing that reads as shippable.
5. Archive hygiene from the 07-22 packaging defects: per-file SHAs inside (R5), no
   AppleDouble/. files (R4), zarr attrs captured verbatim (R2) so downstream holders can
   audit provenance without unpacking anything.

The descriptive block (recipe, provenance, notes) is *declared* by the caller via
``--manifest-json``; everything measurable (file list, sizes, SHAs, attrs capture) is
*computed*. The manifest records which is which.

CLI: mhw-seal <payload_dir> --name <seal-name> [--out DIR] [--manifest-json FILE]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: One canonical provenance string for the OISST observational source (proposed in
#: dashboard-to-admin-…-20260807-01 §5b so F2 closes on a string that matches itself).
OISST_PROVENANCE = (
    "PFEG CoastWatch ERDDAP (ncdcOisst21Agg; NOAA OISST v2.1 Final, AVHRR-Only; "
    "DOI 10.25921/RE9P-PT57)"
)

MANIFEST_NAME = "vintage_manifest.json"
SUMS_NAME = "SHA256SUMS.txt"
ATTRS_NAME = "attrs_verbatim.json"

# ── pure helpers (network-free; unit-tested on small in-memory trees) ──────────────────


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def is_junk(relpath: str) -> bool:
    """AppleDouble/Finder litter — the R4 packaging defect from the 07-22 v1 seal."""
    base = relpath.rsplit("/", 1)[-1]
    return base.startswith("._") or base == ".DS_Store"


def collect_payload(payload_dir: Path) -> list[Path]:
    """Every regular file under the payload dir, junk excluded, deterministic order."""
    return sorted(
        p
        for p in payload_dir.rglob("*")
        if p.is_file() and not is_junk(str(p.relative_to(payload_dir)))
    )


def build_sums(files: list[Path], base: Path) -> str:
    """SHA256SUMS.txt body: ``<sha256>  <relpath>`` per line, sorted by relpath."""
    return (
        "\n".join(f"{sha256_file(p)}  {p.relative_to(base)}" for p in files) + "\n"
    )


def parse_sums(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if line.strip():
            digest, rel = line.split(None, 1)
            out[rel.strip()] = digest
    return out


def capture_zarr_attrs(payload_dir: Path) -> dict[str, dict]:
    """Verbatim per-array attrs for every zarr under the payload (R2).

    Reads zarr metadata as plain JSON files — v3 ``zarr.json`` and v2 ``.zattrs`` —
    so the capture is exactly what a holder would read off the shipped bytes, with no
    library between. Keyed by the metadata file's path relative to the payload root.
    """
    captured: dict[str, dict] = {}
    for store in sorted(payload_dir.rglob("*.zarr")):
        if not store.is_dir():
            continue
        for meta in sorted(list(store.rglob("zarr.json")) + list(store.rglob(".zattrs"))):
            try:
                doc = json.loads(meta.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            attrs = doc.get("attributes") if meta.name == "zarr.json" else doc
            if attrs:
                captured[str(meta.relative_to(payload_dir))] = attrs
    return captured


def build_manifest(
    name: str,
    files: list[Path],
    base: Path,
    declared: dict | None,
    created_utc: str,
) -> dict:
    """The manifest that ships INSIDE the archive. Contains no gates block — verdicts
    about the packed bytes are computed after packing and live in the sidecar."""
    return {
        "seal_name": name,
        "created_utc": created_utc,
        "computed": {
            "n_files": len(files),
            "total_bytes": sum(p.stat().st_size for p in files),
            "files": [str(p.relative_to(base)) for p in files],
        },
        "declared": declared or {},
        "gates_note": (
            "This manifest carries NO gates block by design. Verdicts about the packed "
            "archive are computed from its as-shipped bytes and live in <seal>.gates.json "
            "alongside the tarball (F2 remedy: a gate about the archive cannot live "
            "inside the bytes it measures)."
        ),
    }


# ── packing ─────────────────────────────────────────────────────────────────────────────


def pack(payload_dir: Path, name: str, out_dir: Path, declared: dict | None) -> Path:
    """Stage SUMS + attrs capture + manifest into the payload, then write the tarball.

    Python's tarfile emits no AppleDouble members by construction; junk files are
    excluded by the collector. Deterministic member order (sorted relpaths).
    """
    files = collect_payload(payload_dir)
    if not files:
        raise SystemExit(f"mhw-seal: payload dir {payload_dir} contains no files")

    attrs = capture_zarr_attrs(payload_dir)
    if attrs:
        (payload_dir / ATTRS_NAME).write_text(json.dumps(attrs, indent=2, sort_keys=True))
        files = collect_payload(payload_dir)

    (payload_dir / SUMS_NAME).write_text(build_sums(files, payload_dir))
    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # manifest lists everything that ships except itself — re-collect so SUMS is included
    manifest = build_manifest(name, collect_payload(payload_dir), payload_dir, declared, created)
    (payload_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True))

    out_dir.mkdir(parents=True, exist_ok=True)
    tar_path = out_dir / f"{name}.tar.gz"
    members = collect_payload(payload_dir)  # now includes SUMS + manifest (+ attrs)
    with tarfile.open(tar_path, "w:gz") as tf:
        for p in members:
            tf.add(p, arcname=str(p.relative_to(payload_dir)), recursive=False)
    return tar_path


# ── verification: every gate reads the PACKED archive ──────────────────────────────────


def _gate(name: str, ok: bool, scope: str, evidence: str) -> dict:
    return {
        "gate": name,
        "result": "PASS" if ok else "FAIL",
        "measured_scope": scope,
        "evidence": evidence,
    }


def verify_sealed(tar_path: Path) -> list[dict]:
    """Compute every gate from the as-shipped bytes of ``tar_path``.

    Returns the gate list; callers treat any FAIL as seal-incomplete. Each gate's
    ``measured_scope`` names exactly what was read, per the ratified gate-scope rule.
    """
    scope = f"members of {tar_path.name} read back out of the packed archive"
    gates: list[dict] = []
    with tarfile.open(tar_path, "r:gz") as tf:
        members = {m.name: m for m in tf.getmembers() if m.isfile()}

        def read(name: str) -> bytes:
            f = tf.extractfile(members[name])
            assert f is not None
            return f.read()

        # 1 — hygiene: no AppleDouble/Finder litter (R4)
        junk = sorted(n for n in members if is_junk(n))
        gates.append(
            _gate(
                "no_appledouble_members",
                not junk,
                scope,
                f"{len(members)} members scanned; junk found: {junk or 'none'}",
            )
        )

        # 2 — required records present
        have_sums, have_manifest = SUMS_NAME in members, MANIFEST_NAME in members
        gates.append(
            _gate(
                "required_records_present",
                have_sums and have_manifest,
                scope,
                f"{SUMS_NAME}: {'present' if have_sums else 'MISSING'}; "
                f"{MANIFEST_NAME}: {'present' if have_manifest else 'MISSING'}",
            )
        )
        if not (have_sums and have_manifest):
            return gates

        # 3 — every payload member re-hashed from the archive matches SHA256SUMS.txt
        sums = parse_sums(read(SUMS_NAME).decode())
        payload = [n for n in members if n not in (SUMS_NAME, MANIFEST_NAME)]
        unlisted = sorted(set(payload) - set(sums))
        mismatched = [
            n for n in payload if n in sums and sha256_bytes(read(n)) != sums[n]
        ]
        missing = sorted(set(sums) - set(payload))
        ok = not (unlisted or mismatched or missing)
        gates.append(
            _gate(
                "payload_sha256_match",
                ok,
                scope,
                f"{len(payload)} members re-hashed against {len(sums)} listed; "
                f"mismatched: {mismatched or 'none'}; unlisted: {unlisted or 'none'}; "
                f"listed-but-absent: {missing or 'none'}",
            )
        )

        # 4 — manifest's computed file list == what actually shipped
        manifest = json.loads(read(MANIFEST_NAME).decode())
        declared_files = set(manifest.get("computed", {}).get("files", []))
        actual = set(payload) | {SUMS_NAME}
        # manifest lists the files it was built from: payload + SUMS (+ attrs), not itself
        gates.append(
            _gate(
                "manifest_file_list_matches_archive",
                declared_files == actual,
                scope,
                f"manifest lists {len(declared_files)}; archive ships {len(actual)}; "
                f"only-in-manifest: {sorted(declared_files - actual) or 'none'}; "
                f"only-in-archive: {sorted(actual - declared_files) or 'none'}",
            )
        )

        # 5 — provenance consistency, measured from shipped bytes (the F2 gate done right):
        # runs only when both sides exist INSIDE this archive, and says so either way.
        declared_product = (
            manifest.get("declared", {}).get("provenance", {}).get("product", "")
        )
        if ATTRS_NAME in members and declared_product:
            attrs = json.loads(read(ATTRS_NAME).decode())
            sources = {
                a["source"] for a in attrs.values() if isinstance(a, dict) and "source" in a
            }
            bad = sorted(s for s in sources if s not in declared_product)
            gates.append(
                _gate(
                    "source_attr_matches_declared_product",
                    not bad,
                    f"{ATTRS_NAME} and {MANIFEST_NAME} as shipped in {tar_path.name}",
                    f"distinct source attrs in shipped capture: {sorted(sources) or 'none'}; "
                    f"declared product: {declared_product!r}; non-substring: {bad or 'none'}",
                )
            )
        else:
            gates.append(
                _gate(
                    "source_attr_matches_declared_product",
                    True,
                    "not measured — gate skipped",
                    f"skipped: needs both {ATTRS_NAME} in the archive and "
                    "declared.provenance.product in the manifest; asserting nothing.",
                )
            )
    return gates


def seal(payload_dir: Path, name: str, out_dir: Path, declared: dict | None) -> int:
    """Pack, verify from packed bytes, write sidecar; .sha256 only on all-PASS."""
    tar_path = pack(payload_dir, name, out_dir, declared)
    gates = verify_sealed(tar_path)
    sidecar = out_dir / f"{name}.gates.json"
    sidecar.write_text(
        json.dumps(
            {
                "seal": tar_path.name,
                "outer_sha256": sha256_file(tar_path),
                "verified_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "gates": gates,
            },
            indent=2,
        )
    )
    failed = [g["gate"] for g in gates if g["result"] != "PASS"]
    for g in gates:
        print(f"  {g['result']:4s} {g['gate']}  [{g['measured_scope']}]")
    if failed:
        print(f"mhw-seal: FAILED gates {failed} — no .sha256 written; seal is NOT complete.")
        return 1
    sha_path = tar_path.with_suffix(tar_path.suffix + ".sha256")
    sha_path.write_text(f"{sha256_file(tar_path)}  {tar_path.name}\n")
    print(f"mhw-seal: sealed {tar_path.name} ({sha_path.name} written; gates in {sidecar.name})")
    return 0


# ── CLI ─────────────────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="mhw-seal",
        description="Package a payload directory as a sealed tarball with gates "
        "computed from the as-shipped bytes.",
    )
    ap.add_argument("payload", type=Path, help="directory whose contents form the seal")
    ap.add_argument("--name", required=True, help="seal name (tarball stem)")
    ap.add_argument(
        "--out", type=Path, default=PROJECT_ROOT / "data" / "seals", help="output dir"
    )
    ap.add_argument(
        "--manifest-json",
        type=Path,
        default=None,
        help="JSON file with the DECLARED block (recipe, provenance, notes); "
        "everything measurable is computed regardless",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    declared = json.loads(args.manifest_json.read_text()) if args.manifest_json else None
    return seal(args.payload.resolve(), args.name, args.out.resolve(), declared)


if __name__ == "__main__":
    sys.exit(main())
