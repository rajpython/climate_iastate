"""Access control for the assistant — the single switch point.

`enforce_access` is the ONLY gate. In the default **open + capped** posture it applies a per-client
rate limit and a hard monthly token budget (so a public chatbot can't run up an unbounded bill).
Flipping to **gated** later is a one-place change: set ``ASSISTANT_ACCESS_MODE=gated`` (+ a
password) and this function additionally requires it — nothing else in the service changes.

Env:
    ASSISTANT_ACCESS_MODE        open | gated              (default open)
    ASSISTANT_GATE_PASSWORD      shared password           (gated mode only)
    ASSISTANT_RATE_PER_MIN       requests/client/minute    (default 20)
    ASSISTANT_MONTHLY_TOKEN_BUDGET  hard monthly cap        (default 5_000_000)
    ASSISTANT_MAX_TOOL_ITERS     tool-loop cap per turn     (default 8)
    ASSISTANT_BUDGET_FILE        month-keyed JSON counter   (default data/derived/assistant_budget.json)
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_BUDGET_FILE = PROJECT_ROOT / "data" / "derived" / "assistant_budget.json"


class AccessError(Exception):
    """Raised when a request is refused. ``status_code`` maps straight to the HTTP response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@dataclass
class AccessSettings:
    mode: str = "open"                       # "open" | "gated"
    gate_password: str | None = None
    rate_per_min: int = 20
    monthly_token_budget: int = 5_000_000
    max_tool_iterations: int = 24            # headroom for decomposed, multi-part (compound) requests

    @classmethod
    def from_env(cls) -> "AccessSettings":
        return cls(
            mode=os.getenv("ASSISTANT_ACCESS_MODE", "open").strip().lower(),
            gate_password=(os.getenv("ASSISTANT_GATE_PASSWORD") or None),
            rate_per_min=int(os.getenv("ASSISTANT_RATE_PER_MIN", "20")),
            monthly_token_budget=int(os.getenv("ASSISTANT_MONTHLY_TOKEN_BUDGET", "5000000")),
            max_tool_iterations=int(os.getenv("ASSISTANT_MAX_TOOL_ITERS", "24")),
        )


class RateLimiter:
    """Sliding 60-second per-client request limiter (in-process, thread-safe)."""

    def __init__(self, max_per_min: int):
        self.max = max_per_min
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, client_id: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            window = [t for t in self._hits.get(client_id, []) if now - t < 60.0]
            if len(window) >= self.max:
                self._hits[client_id] = window
                return False
            window.append(now)
            self._hits[client_id] = window
            return True


class BudgetTracker:
    """Persistent month-keyed token counter (survives restarts via a small JSON file)."""

    def __init__(self, path: Path, monthly_limit: int):
        self.path = Path(path)
        self.limit = monthly_limit
        self._lock = threading.Lock()

    @staticmethod
    def _month_key(now: float | None = None) -> str:
        t = time.gmtime(now)
        return f"{t.tm_year:04d}-{t.tm_mon:02d}"

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, ValueError):
            return {}

    def used(self, now: float | None = None) -> int:
        return int(self._load().get(self._month_key(now), 0))

    def over_budget(self, now: float | None = None) -> bool:
        return self.used(now) >= self.limit

    def add(self, tokens: int, now: float | None = None) -> int:
        with self._lock:
            data = self._load()
            key = self._month_key(now)
            data[key] = int(data.get(key, 0)) + int(tokens)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data))
            return data[key]


# Module-level singletons wired from the environment (overridable in tests via args).
_SETTINGS = AccessSettings.from_env()
_RATE = RateLimiter(_SETTINGS.rate_per_min)
_BUDGET = BudgetTracker(
    Path(os.getenv("ASSISTANT_BUDGET_FILE", str(_DEFAULT_BUDGET_FILE))),
    _SETTINGS.monthly_token_budget,
)


def budget_tracker() -> BudgetTracker:
    return _BUDGET


def settings() -> AccessSettings:
    return _SETTINGS


def enforce_access(
    client_id: str,
    password: str | None = None,
    *,
    settings: AccessSettings | None = None,
    rate: RateLimiter | None = None,
    budget: BudgetTracker | None = None,
) -> None:
    """Refuse a request by raising ``AccessError``; return ``None`` if allowed.

    Order: gate (gated mode only) → per-client rate limit → monthly token budget.
    """
    settings = settings or _SETTINGS
    rate = rate or _RATE
    budget = budget or _BUDGET

    if settings.mode == "gated":
        if not settings.gate_password or password != settings.gate_password:
            raise AccessError(403, "Access is gated — a valid password is required.")

    if not rate.check(client_id):
        raise AccessError(429, "Rate limit exceeded — please slow down and retry shortly.")

    if budget.over_budget():
        raise AccessError(
            429,
            "Monthly usage budget reached — the assistant is paused until next month.",
        )
