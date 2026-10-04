"""Execution records — bind a build to the bytes it actually OPENED, not to a declared list.

CLI: mhw-exec-record wrap --out DIR [--declared SHAS.txt] -- <command ...>
     mhw-exec-record finalize --log RUN.jsonl --out DIR [--declared SHAS.txt]

Why this exists (dashboard audit D01, 2026-10-03)
-------------------------------------------------
Vintage #6's records generator (``docs/provenance/.../write_records_v6.py``, kept unchanged as
historical evidence) carried the input file list forward from vintage #5. The build had in fact
opened September-extended copies of the twelve ``oisst_<zone>_2026.nc`` files: same names,
different bytes. Nothing in the record could see that, because nothing in it was measured at
the moment of use. This module is the successor mechanism.

How it works
------------
* Instrumented call sites (below) call :func:`record_open` immediately BEFORE they open an
  input, :func:`record_use` for what part of it was processed (requested / available /
  processed dates: an intended calendar restriction is visible, not hidden), and
  :func:`record_missing` for a dependency looked for and absent. When ``MHW_EXEC_RECORD`` names a JSONL log, one line is appended per distinct
  (path, size, mtime_ns): role, absolute path, basename, sha256, size, mtime. With the variable
  unset the call is a no-op, so production paths are unaffected.
* Directories (zarr stores) are hashed with the same recipe the vintage lists use for
  aggregates: ``sha256('\\n'.join(sorted('<relpath>:<sha256>')))``.
* :func:`finalize` turns the log into ``executed_inputs.json`` plus a
  ``oisst_input_file_shas_executed.txt`` in the vintage-list format (``<basename>:<sha256>``,
  with the same aggregate recipe). Given ``--declared``, it compares by NAME and by BYTES and
  fails (exit 3) on any same-name/different-hash file: that is exactly the D01 condition.
* ``wrap`` refuses a non-empty output directory (exit 5), sets the variable, runs the command and
  ALWAYS finalizes. Every record carries a durable ``status`` / ``exit_code`` / ``command_exit_status``:
  OK (0); RECORD_CHECK_FAILED (3); NO_EXECUTED_INPUTS (4: nothing instrumented was opened, including
  missing-only or code-only logs, so an uninstrumented entry point cannot read as complete);
  COMMAND_FAILED (the child's own non-zero exit, which is also the wrapper's). Only the leading ``--``
  is consumed; later ``--`` tokens belong to the child.
* Raw inputs are keyed by resolved path. Two opened paths with one basename and different bytes are
  ambiguous against a basename-keyed list: both are listed and the record fails (auditor finding on
  b2b8d151, 2026-10-04).

Instrumented call sites (enforced only when the variable is set, i.e. under ``wrap``)
------------------------------------------------------------------------------------
``build_mu_theta.fetch_year`` (every zone-year OISST cache file the climatology build and the
state engine read) · ``ice_outage._ice_on`` (bracketing files resolved dynamically around
outage runs) · ``build_mu_theta._load_config`` / ``_load_region_bbox`` · ``ice_outage``
outage config · ``update_states._load_climatology`` (theta90/mu stores) ·
``aggregates._load_states`` / ``_load_mask_weights`` / ``load_filled_days``.

Known gaps (stated, not hidden)
-------------------------------
* Mutation: each input is hashed just before it is opened, and ``finalize`` re-hashes every
  opened path; any difference (or a vanished file) fails the record (exit 3). This detects a change
  between open and the end of the run. It cannot detect a change that is made and then exactly
  reverted between those two hashes, nor prove the bytes read equal the bytes hashed at the instant
  of reading; frozen caches are also made read-only (``chmod a-w``) by procedure.
* Entry points outside the list above (``mhw-update-ncei``, ``mhw-compute-risk``, the bottom/
  forecast/econ modules, the dashboard and API readers) are NOT instrumented.
* A record binds files; it does not bind the Python environment beyond what ``finalize``
  captures (interpreter, platform, git HEAD + dirty flag, key package versions).
"""
from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_VAR = "MHW_EXEC_RECORD"

_SEEN: set[tuple[str, int, int]] = set()
_CODE_HOOKED = False


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def aggregate_sha(pairs: list[str]) -> str:
    """The vintage-list aggregate recipe: sha256('\\n'.join(sorted(pairs))), no trailing newline."""
    return hashlib.sha256("\n".join(sorted(pairs)).encode()).hexdigest()


def sha256_path(path: Path) -> str:
    """File: its sha256. Directory (zarr store): aggregate over '<relpath>:<sha256>' of every file."""
    path = Path(path)
    if path.is_dir():
        pairs = [f"{p.relative_to(path).as_posix()}:{sha256_file(p)}"
                 for p in sorted(path.rglob("*")) if p.is_file()]
        return aggregate_sha(pairs)
    return sha256_file(path)


def parse_shas_list(text: str) -> dict[str, str]:
    """Read a '<basename>:<sha256>' list (comment lines '#' ignored) -> {basename: sha256}."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        name, sha = line.rsplit(":", 1)
        out[name] = sha
    return out


def compare_to_declared(executed: dict[str, str], declared: dict[str, str]) -> dict:
    """Compare executed vs declared by name AND bytes. ``changed`` = same name, different hash (D01)."""
    common = sorted(set(executed) & set(declared))
    changed = [n for n in common if executed[n] != declared[n]]
    return {
        "n_executed": len(executed), "n_declared": len(declared),
        "n_same_name_same_bytes": len(common) - len(changed),
        "changed_same_name_different_bytes": changed,
        "executed_not_declared": sorted(set(executed) - set(declared)),
        "declared_not_executed": sorted(set(declared) - set(executed)),
        "ok": not changed,
    }


def read_log(log: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """-> (opened, uses, missing). Opened rows are unique per (path, sha): a file opened by several
    processes is recorded once; a path seen with two different hashes is kept twice (a conflict)."""
    rows = [json.loads(line) for line in Path(log).read_text().splitlines() if line.strip()]
    uniq: dict[tuple[str, str], dict] = {}
    for r in rows:
        if r.get("event", "open") == "open":
            uniq.setdefault((r["path"], r["sha256"]), r)
    opened = sorted(uniq.values(), key=lambda r: (r["role"], r["path"]))
    uses = [r for r in rows if r.get("event") in ("use", "code")]
    missing = sorted({(r["role"], r["path"]): r for r in rows if r.get("event") == "missing"}.values(),
                     key=lambda r: (r["role"], r["path"]))
    return opened, uses, missing


def verify_unchanged(opened: list[dict]) -> list[dict]:
    """Re-hash every opened path NOW. A file whose bytes differ from its at-open hash (or that has
    vanished) was mutated during or after the run: the record cannot vouch for what was processed."""
    bad = []
    for r in opened:
        p = Path(r["path"])
        now = sha256_path(p) if p.exists() else None
        if now != r["sha256"]:
            bad.append({"path": r["path"], "at_open": r["sha256"], "at_finalize": now})
    return bad


# ---------------------------------------------------------------------------
# Recording (called by the pipeline)
# ---------------------------------------------------------------------------
def _append(row: dict) -> None:
    log = os.environ.get(ENV_VAR)
    if not log:
        return
    row = {**row, "pid": os.getpid(), "recorded_utc": datetime.now(timezone.utc).isoformat()}
    with open(log, "a") as f:
        f.write(json.dumps(row) + "\n")


def record_use(path, role: str, **detail) -> None:
    """Record what part of an opened input was USED (e.g. requested/available/processed dates)."""
    if os.environ.get(ENV_VAR):
        _append({"event": "use", "role": role, "path": str(Path(path).resolve()), **detail})


def record_missing(path, role: str) -> None:
    """Record a dependency that was looked for and absent (a tolerated miss or a fatal one)."""
    if os.environ.get(ENV_VAR):
        _append({"event": "missing", "role": role, "path": str(Path(path).resolve())})


def _record_code() -> None:
    """At process exit: sha256 of every module file this process actually imported from the project
    (plus interpreter and argv). Written at exit so lazily imported helpers are included."""
    src = (PROJECT_ROOT / "src").resolve()
    mods = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if f and Path(f).resolve().is_relative_to(src) and Path(f).exists():
            mods[Path(f).resolve().relative_to(src).as_posix()] = sha256_file(Path(f))
    commit = PROJECT_ROOT / "FIXTURE_COMMIT"
    _append({"event": "code", "argv": sys.argv, "python": sys.version.split()[0],
             "executable": sys.executable, "project_root": str(PROJECT_ROOT),
             "export_commit": commit.read_text().strip() if commit.exists() else None,
             "modules": dict(sorted(mods.items()))})


def record_open(path, role: str) -> None:
    """Append (role, path, sha256, size, mtime) to $MHW_EXEC_RECORD before *path* is opened."""
    global _CODE_HOOKED
    log = os.environ.get(ENV_VAR)
    if not log:
        return
    if not _CODE_HOOKED:
        _CODE_HOOKED = True
        atexit.register(_record_code)
    p = Path(path).resolve()
    if not p.exists():
        return
    st = p.stat()
    key = (str(p), st.st_size, st.st_mtime_ns)
    if key in _SEEN:
        return
    _SEEN.add(key)
    _append({"event": "open", "role": role, "path": str(p), "basename": p.name,
             "sha256": sha256_path(p), "is_dir": p.is_dir(), "size": st.st_size,
             "mtime_ns": st.st_mtime_ns})


# ---------------------------------------------------------------------------
# Finalize
# ---------------------------------------------------------------------------
def _environment() -> dict:
    def git(*a):
        try:
            return subprocess.check_output(["git", "-C", str(PROJECT_ROOT), *a],
                                           stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return None
    pk = {}
    for name in ("numpy", "xarray", "pandas", "zarr", "netCDF4", "scipy"):
        try:
            pk[name] = __import__(name).__version__
        except Exception:
            pk[name] = None
    return {"host": socket.gethostname(), "python": sys.version.split()[0],
            "platform": platform.platform(), "executable": sys.executable,
            "project_root": str(PROJECT_ROOT), "git_head": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
            "packages": pk,
            "env": {k: os.environ.get(k) for k in ("MHW_FROZEN_INPUTS", ENV_VAR)}}


RAW_ROLES = ("raw_sst_ice", "raw_ice_bracket")
EXIT_OK, EXIT_CHECK_FAILED, EXIT_NO_INPUTS, EXIT_OUT_NOT_EMPTY = 0, 3, 4, 5


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def finalize(log: Path, out: Path, declared: Path | None = None,
             command: list[str] | None = None, command_exit: int | None = None) -> int:
    """Write the execution record. ALWAYS writes one (even for a failed or empty run) with a durable
    ``status`` and ``exit_code``, so a record can never read as a success it was not.

    Exit precedence: a failed command's own exit > 4 (no executed inputs) > 3 (a check failed) > 0.
    Refuses (exit 5, writes nothing) when *out* already holds a record: a reused directory must not
    leave an earlier run's record in place under a new run's name.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "executed_inputs.json").exists():
        print(f"mhw-exec-record: {out} already holds a record; refusing to overwrite (use a fresh "
              "directory)", file=sys.stderr)
        return EXIT_OUT_NOT_EMPTY
    rows, uses, missing = read_log(log)
    by_path: dict[str, set] = {}
    for r in rows:
        by_path.setdefault(r["path"], set()).add(r["sha256"])
    conflicts = sorted(p for p, s in by_path.items() if len(s) > 1)
    mutated = verify_unchanged(rows)
    code_rows = [u for u in uses if u.get("event") == "code"]
    uses = [u for u in uses if u.get("event") == "use"]
    executed_code: dict[str, set] = {}
    for c in code_rows:
        for f, h in c["modules"].items():
            executed_code.setdefault(f, set()).add(h)
    code_conflicts = sorted(f for f, h in executed_code.items() if len(h) > 1)
    code_pairs = [f"{f}:{h}" for f, hs in executed_code.items() for h in sorted(hs)]
    use_by_path: dict[str, list] = {}
    for u in uses:
        use_by_path.setdefault(u["path"], []).append(
            {k: v for k, v in u.items() if k not in ("event", "path", "role", "pid", "recorded_utc")})
    for r in rows:
        if r["path"] in use_by_path:
            r["use"] = use_by_path[r["path"]]

    # Raw inputs are keyed by RESOLVED PATH. The vintage-list format is by basename, so two distinct
    # opened paths sharing a basename with different bytes are AMBIGUOUS against any basename list:
    # both are listed, and the record fails rather than collapsing them into one entry.
    raw = [r for r in rows if r["role"] in RAW_ROLES]
    by_base: dict[str, set] = {}
    for r in raw:
        by_base.setdefault(r["basename"], set()).add(r["sha256"])
    ambiguous = sorted(b for b, h in by_base.items() if len(h) > 1)
    pairs = sorted({f"{r['basename']}:{r['sha256']}" for r in raw})
    unambiguous = {b: next(iter(h)) for b, h in by_base.items() if len(h) == 1}

    checks: dict = {"paths_with_conflicting_hashes": conflicts, "mutated_after_open": mutated,
                    "code_modules_at_two_versions": code_conflicts,
                    "basenames_opened_with_different_bytes": ambiguous}
    if declared:
        cmp = compare_to_declared(unambiguous, parse_shas_list(Path(declared).read_text()))
        cmp["ambiguous_basenames"] = ambiguous
        cmp["ok"] = cmp["ok"] and not ambiguous
        cmp["declared_file"] = str(declared)
        cmp["declared_file_sha256"] = sha256_file(Path(declared))
        checks["declared_comparison"] = cmp
    check_failed = bool(conflicts or mutated or code_conflicts or ambiguous
                        or (declared and not checks["declared_comparison"]["ok"]))

    statuses = []
    if command_exit not in (None, 0):
        statuses.append("COMMAND_FAILED")
    if not rows:
        statuses.append("NO_EXECUTED_INPUTS")
    if check_failed:
        statuses.append("RECORD_CHECK_FAILED")
    if command_exit not in (None, 0):
        rc = int(command_exit)
    elif not rows:
        rc = EXIT_NO_INPUTS
    elif check_failed:
        rc = EXIT_CHECK_FAILED
    else:
        rc = EXIT_OK
    status = statuses[0] if statuses else "OK"

    rec = {
        "record_type": "execution_record", "generator": "mhw.exec_record (successor to write_records_v*.py)",
        "written_utc": datetime.now(timezone.utc).isoformat(), "command": command,
        "status": status, "all_statuses": statuses or ["OK"], "exit_code": rc,
        "command_exit_status": command_exit,
        "environment": _environment(), "n_opened": len(rows), "n_raw_inputs": len(raw),
        "checks": checks,
        "executed_code": {"processes": [{k: c.get(k) for k in ("argv", "python", "executable", "project_root",
                                                              "export_commit", "pid")} for c in code_rows],
                          "n_module_files": len(executed_code),
                          "aggregate_sha256": aggregate_sha(code_pairs),
                          "files": {f: sorted(h) for f, h in sorted(executed_code.items())},
                          "conflicting_versions": code_conflicts},
        "missing_dependencies": [{"role": m["role"], "path": m["path"]} for m in missing],
        "verdict_rules": (
            "status OK (exit 0) only if: >=1 input was opened; no path seen with two hashes; no opened input "
            "changed between open and finalize; no module ran at two versions; no basename opened with two "
            "different byte contents; and, with --declared, every declared basename's bytes equal. "
            "NO_EXECUTED_INPUTS (exit 4): nothing instrumented was opened -- missing-only or code-only logs "
            "included. Missing dependencies alongside opened inputs are LISTED, not failed (some are optional "
            "by design, e.g. the ice-outage bracket search). COMMAND_FAILED: the wrapped command's own non-zero "
            "exit, which is also the wrapper's exit."),
        "raw_inputs": {"n_paths": len(raw), "n_distinct_basename_sha_pairs": len(pairs),
                       "aggregate_sha256": aggregate_sha(pairs),
                       "aggregate_recipe": "sha256('\\n'.join(sorted(set('<basename>:<sha256>')))), no trailing newline",
                       "by_path": [{"path": r["path"], "basename": r["basename"], "sha256": r["sha256"],
                                    "role": r["role"]} for r in raw]},
        "opened": rows,
    }
    hdr = [f"# EXECUTED inputs: hashed at open time by mhw.exec_record; status={status}; exit_code={rc}; "
           f"command_exit_status={command_exit}",
           f"# n_paths={len(raw)} n_pairs={len(pairs)} ambiguous_basenames={','.join(ambiguous) or '-'}",
           f"# aggregate_executed_{len(pairs)}={aggregate_sha(pairs)}",
           "# aggregate recipe: sha256( '\\n'.join(sorted(set('<basename>:<sha256>'))) ), no trailing newline"]
    _atomic_write(out / "oisst_input_file_shas_executed.txt", "\n".join(hdr + pairs) + "\n")
    _atomic_write(out / "executed_inputs.json", json.dumps(rec, indent=1) + "\n")   # written LAST
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="mhw-exec-record", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("wrap", help="run a command with recording on, then finalize")
    w.add_argument("--out", required=True, type=Path)
    w.add_argument("--declared", type=Path, default=None)
    w.add_argument("command", nargs=argparse.REMAINDER)
    f = sub.add_parser("finalize", help="turn a JSONL log into an execution record")
    f.add_argument("--log", required=True, type=Path)
    f.add_argument("--out", required=True, type=Path)
    f.add_argument("--declared", type=Path, default=None)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    if a.cmd == "finalize":
        rc = finalize(a.log, a.out, a.declared)
        print(f"mhw-exec-record: finalize rc={rc}; {a.out}/executed_inputs.json")
        return rc
    # Only the separator between the wrapper's options and the command is consumed; any later "--" is
    # the child's own argument and is passed through untouched.
    cmd = list(a.command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("mhw-exec-record wrap: no command given", file=sys.stderr)
        return 2
    if a.out.exists() and any(a.out.iterdir()):
        print(f"mhw-exec-record wrap: {a.out} is not empty; refusing to run (an earlier record there "
              "could be read as this run's). Use a fresh directory.", file=sys.stderr)
        return EXIT_OUT_NOT_EMPTY
    a.out.mkdir(parents=True, exist_ok=True)
    log = a.out / "opened.jsonl"
    log.touch()
    env = dict(os.environ, **{ENV_VAR: str(log)})
    rc_cmd = subprocess.call(cmd, env=env)
    rc = finalize(log, a.out, a.declared, command=cmd, command_exit=rc_cmd)
    if rc == EXIT_NO_INPUTS:
        print("mhw-exec-record wrap: the command opened NO instrumented input (record status "
              "NO_EXECUTED_INPUTS; uninstrumented entry point?)", file=sys.stderr)
    print(f"mhw-exec-record: command rc={rc_cmd}; exit {rc}; {a.out}/executed_inputs.json")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
