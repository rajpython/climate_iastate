"""Dashboard region-listing tests — the unified bottom-state region list (no network)."""
from __future__ import annotations

from dashboard.components import coldpool_data as cd


def test_list_bottom_state_regions_unions_coldpool_and_bottom_temp(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    model = tmp_path / "model"
    raw.mkdir()
    model.mkdir()
    # EBS appears via its observed cold-pool index; the slope via a built bottom-temp model.
    (raw / "coldpool_index_observed_sebs.parquet").write_bytes(b"")
    (model / "coldpool_model_bering10k_slope.parquet").write_bytes(b"")

    monkeypatch.setattr(cd, "RAW_DIR", raw)
    monkeypatch.setattr(cd, "MODEL_DIR", model)
    cd.list_bottom_state_regions.clear()

    regs = cd.list_bottom_state_regions()
    # both kinds present, in south→north order (EBS before the slope)
    assert regs == ["sebs", "slope"]


def test_list_bottom_state_regions_excludes_unbuilt_bottom_temp(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    model = tmp_path / "model"
    raw.mkdir()
    model.mkdir()
    (raw / "coldpool_index_observed_sebs.parquet").write_bytes(b"")
    # no slope model on disk -> slope must NOT appear

    monkeypatch.setattr(cd, "RAW_DIR", raw)
    monkeypatch.setattr(cd, "MODEL_DIR", model)
    cd.list_bottom_state_regions.clear()

    assert cd.list_bottom_state_regions() == ["sebs"]
