"""Access-gate unit tests — the single guard must enforce rate, budget, and gated password."""
from __future__ import annotations

import pytest

from mhw.assistant.access import (
    AccessError,
    AccessSettings,
    BudgetTracker,
    RateLimiter,
    enforce_access,
)


def test_rate_limiter_blocks_after_max_then_slides():
    rl = RateLimiter(max_per_min=2)
    assert rl.check("c", now=1000.0)
    assert rl.check("c", now=1000.1)
    assert not rl.check("c", now=1000.2)      # third within the window is blocked
    assert rl.check("c", now=1061.0)          # window slid past 60 s


def test_budget_tracker_persists_and_trips(tmp_path):
    bt = BudgetTracker(tmp_path / "b.json", monthly_limit=100)
    assert not bt.over_budget(now=0.0)
    bt.add(60, now=0.0)
    bt.add(50, now=0.0)
    assert bt.over_budget(now=0.0)
    # A fresh tracker reads the same file back (persistence).
    assert BudgetTracker(tmp_path / "b.json", 100).used(now=0.0) == 110


def _rl_bt(tmp_path, rate=5, budget=1000):
    return RateLimiter(rate), BudgetTracker(tmp_path / "b.json", budget)


def test_enforce_open_allows(tmp_path):
    s = AccessSettings(mode="open", rate_per_min=5, monthly_token_budget=1000)
    rl, bt = _rl_bt(tmp_path)
    enforce_access("c", settings=s, rate=rl, budget=bt)   # no raise


def test_enforce_gated_requires_password(tmp_path):
    s = AccessSettings(mode="gated", gate_password="secret", rate_per_min=5, monthly_token_budget=1000)
    rl, bt = _rl_bt(tmp_path)
    with pytest.raises(AccessError) as exc:
        enforce_access("c", password="wrong", settings=s, rate=rl, budget=bt)
    assert exc.value.status_code == 403
    enforce_access("c", password="secret", settings=s, rate=rl, budget=bt)  # correct → ok


def test_enforce_rate_limit_429(tmp_path):
    s = AccessSettings(mode="open", rate_per_min=1, monthly_token_budget=1000)
    rl, bt = _rl_bt(tmp_path, rate=1)
    enforce_access("c", settings=s, rate=rl, budget=bt)
    with pytest.raises(AccessError) as exc:
        enforce_access("c", settings=s, rate=rl, budget=bt)
    assert exc.value.status_code == 429


def test_enforce_budget_429(tmp_path):
    s = AccessSettings(mode="open", rate_per_min=5, monthly_token_budget=10)
    rl, bt = _rl_bt(tmp_path, budget=10)
    bt.add(20)
    with pytest.raises(AccessError) as exc:
        enforce_access("c", settings=s, rate=rl, budget=bt)
    assert exc.value.status_code == 429
