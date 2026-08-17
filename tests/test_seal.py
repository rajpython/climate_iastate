"""Tests for mhw.seal — the scripted seal builder (F2 remedy).

The load-bearing property is negative: a seal whose shipped bytes disagree with its
records must FAIL verification, because the whole point is that PASS can no longer be
typed. So alongside the happy path we tamper with a packed archive and require the
gate to catch it, and we require that no .sha256 exists after a failed seal.
"""
from __future__ import annotations

import gzip
import json
import tarfile

import pytest

from mhw.seal import (
    ATTRS_NAME,
    MANIFEST_NAME,
    SUMS_NAME,
    build_sums,
    capture_zarr_attrs,
    collect_payload,
    is_junk,
    parse_sums,
    seal,
    sha256_file,
    verify_sealed,
)


@pytest.fixture()
def payload(tmp_path):
    p = tmp_path / "payload"
    (p / "sub").mkdir(parents=True)
    (p / "a.parquet").write_bytes(b"alpha" * 100)
    (p / "sub" / "b.nc").write_bytes(b"bravo" * 200)
    (p / "._junk").write_bytes(b"appledouble")
    (p / ".DS_Store").write_bytes(b"finder")
    # minimal zarr-v3 store: one array metadata file carrying a source attr
    z = p / "theta90_sebs.zarr" / "theta90"
    z.mkdir(parents=True)
    (z / "zarr.json").write_text(
        json.dumps({"attributes": {"source": "PFEG CoastWatch ERDDAP", "region": "sebs"}})
    )
    return p


def _gate(gates, name):
    return next(g for g in gates if g["gate"] == name)


def test_junk_detection():
    assert is_junk("._foo") and is_junk("dir/.DS_Store") and not is_junk("data.nc")


def test_collect_payload_excludes_junk_and_sorts(payload):
    rels = [str(f.relative_to(payload)) for f in collect_payload(payload)]
    assert "._junk" not in rels and ".DS_Store" not in rels
    assert rels == sorted(rels)


def test_sums_roundtrip(payload):
    files = collect_payload(payload)
    parsed = parse_sums(build_sums(files, payload))
    assert parsed["a.parquet"] == sha256_file(payload / "a.parquet")
    assert len(parsed) == len(files)


def test_capture_zarr_attrs(payload):
    cap = capture_zarr_attrs(payload)
    key = "theta90_sebs.zarr/theta90/zarr.json"
    assert cap[key]["source"] == "PFEG CoastWatch ERDDAP"


def test_seal_happy_path(payload, tmp_path, capsys):
    out = tmp_path / "out"
    declared = {"provenance": {"product": "PFEG CoastWatch ERDDAP (ncdcOisst21Agg)"}}
    assert seal(payload, "test-seal", out, declared) == 0
    tar = out / "test-seal.tar.gz"
    assert tar.exists() and (out / "test-seal.tar.gz.sha256").exists()

    gates_doc = json.loads((out / "test-seal.gates.json").read_text())
    results = {g["gate"]: g["result"] for g in gates_doc["gates"]}
    assert set(results.values()) == {"PASS"}
    # every gate names what it measured — the ratified gate-scope rule
    assert all(g["measured_scope"] for g in gates_doc["gates"])
    # gates live in the sidecar, never inside the archive's manifest
    with tarfile.open(tar) as tf:
        manifest = json.load(tf.extractfile(MANIFEST_NAME))
        names = tf.getnames()
    assert "gates" not in manifest
    assert SUMS_NAME in names and ATTRS_NAME in names
    assert not any(is_junk(n) for n in names)
    # outer sha in sidecar matches the tarball on disk
    assert gates_doc["outer_sha256"] == sha256_file(tar)


def test_tampered_archive_fails_and_writes_no_sha256(payload, tmp_path):
    """Repack the sealed tarball with one payload byte changed: the SHA gate must
    FAIL against the records the archive itself carries."""
    out = tmp_path / "out"
    assert seal(payload, "tamper", out, None) == 0
    tar = out / "tamper.tar.gz"

    # rebuild the archive, flipping a.parquet's content, keeping SUMS/manifest as-is
    stage = tmp_path / "stage"
    with tarfile.open(tar) as tf:
        tf.extractall(stage, filter="data")
    (stage / "a.parquet").write_bytes(b"TAMPERED")
    with tarfile.open(tar, "w:gz") as tf:
        for f in sorted(stage.rglob("*")):
            if f.is_file():
                tf.add(f, arcname=str(f.relative_to(stage)), recursive=False)

    gates = verify_sealed(tar)
    sha_gate = _gate(gates, "payload_sha256_match")
    assert sha_gate["result"] == "FAIL"
    assert "a.parquet" in sha_gate["evidence"]
    assert "read back out of the packed archive" in sha_gate["measured_scope"]


def test_failed_seal_writes_no_sha256(payload, tmp_path, monkeypatch):
    """If any gate fails, no .sha256 may exist — nothing shippable-looking remains."""
    import mhw.seal as sealmod

    out = tmp_path / "out"
    monkeypatch.setattr(
        sealmod, "verify_sealed", lambda t: [
            {"gate": "forced", "result": "FAIL", "measured_scope": "test", "evidence": "forced"}
        ],
    )
    assert sealmod.seal(payload, "failing", out, None) == 1
    assert not (out / "failing.tar.gz.sha256").exists()
    assert (out / "failing.gates.json").exists()  # the FAIL is still on record


def test_source_attr_gate_fails_on_mismatch(payload, tmp_path):
    out = tmp_path / "out"
    declared = {"provenance": {"product": "NOAA PSL THREDDS OPeNDAP"}}  # the F2 string
    rc = seal(payload, "f2-replay", out, declared)
    gates = json.loads((out / "f2-replay.gates.json").read_text())["gates"]
    g = _gate(gates, "source_attr_matches_declared_product")
    assert g["result"] == "FAIL" and rc == 1
    assert not (out / "f2-replay.tar.gz.sha256").exists()


def test_source_attr_gate_skips_honestly_without_inputs(tmp_path):
    p = tmp_path / "plain"
    p.mkdir()
    (p / "data.txt").write_bytes(b"no zarr here")
    out = tmp_path / "out"
    assert seal(p, "plain", out, None) == 0
    g = _gate(
        json.loads((out / "plain.gates.json").read_text())["gates"],
        "source_attr_matches_declared_product",
    )
    assert g["measured_scope"] == "not measured — gate skipped"
    assert "asserting nothing" in g["evidence"]


def test_corrupt_gzip_raises(payload, tmp_path):
    out = tmp_path / "out"
    seal(payload, "corrupt", out, None)
    tar = out / "corrupt.tar.gz"
    tar.write_bytes(tar.read_bytes()[: tar.stat().st_size // 2])
    with pytest.raises((tarfile.ReadError, gzip.BadGzipFile, EOFError)):
        verify_sealed(tar)
