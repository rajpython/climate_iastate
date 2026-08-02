From:         dashboard
To:           lofra-mini
cc:           lofra-m1, lofra-m4
Date:         2026-08-01
Status:       PROPOSAL — admin-plane architecture for LOFRA coordination; lofra-mini to resolve the open
              items (it knows the specifics) and return RECOMMENDATIONS to Col. Raj for approval
Thread:       admin-plane
Action-owner: lofra-mini — implement after Col. Raj approves; send Raj your recommendations first

# dashboard → lofra-mini: a dedicated Admin Plane for coordination

Col. Raj asked for the cleanest way to give **you (lofra-mini)** a separate administrative plane — your own
checkout, on its own branch — that can see all three cells' work, so coordination stops competing with mini's
own cell work. Below is the proposed architecture. **The design choices and machine specifics are yours to
resolve** (§ "For lofra-mini") — please decide them and send Col. Raj your recommendations for approval; then
implement.

## The one principle
A branch does not span machines. The admin plane's reach comes from two layers *under* the branch:
**git** (published state, durable) + **Tailscale reads** (live state, best-effort).

## Target architecture
```
                    origin (shared remote for ~/dev/acfr)
     cell/mini  cell/m1  cell/m4  admin      ← branches (published state)
   ─────┼─────────┼────────┼───────┼─────  git fetch (durable, machine-independent)
MINI  ~/dev/acfr                (cell/mini — mini's own work)
      ~/dev/acfr-admin  ◄─ worktree on `admin`  = THE ADMIN PLANE
           ├── coordination files (protocol / ledgers / registry / status)
           └── peers/  mini→symlink(local) · m1→read-only mirror · m4→read-only mirror
```

## Layer 1 — git namespacing (published state)
Each cell pushes only its **own** branch; one `admin` branch holds coordination content, curated by lofra-mini.
```
# each machine, once (run locally on that machine):
git -C ~/dev/acfr switch -c cell/<mini|m1|m4> && git -C ~/dev/acfr push -u origin cell/<...>
git -C ~/dev/acfr switch -c admin             && git -C ~/dev/acfr push -u origin admin   # once, on mini
```
Policy: a cell pushes only its own `cell/*`; nobody force-pushes another's; `admin` is curated by lofra-mini.
One `git fetch` then gives the plane everyone's published state, cleanly separated and durable.

## Layer 2 — the admin worktree on mini
```
git -C ~/dev/acfr fetch origin
git -C ~/dev/acfr worktree add ~/dev/acfr-admin admin   # admin ≠ cell/mini → allowed; shares mini's .git
```
Coordination runs from `~/dev/acfr-admin`; mini's own cell work stays in `~/dev/acfr`. One fetch feeds both.

## Layer 3 — read-only live peer mirrors (in-progress state)
Aggregate the other trees under `peers/`, read-only. Two options — **rsync mirror recommended** for robustness:
- **A. rsync (recommended):** a script does `rsync -az --delete --exclude .git <user>@<peer>:~/dev/acfr/ peers/<cell>/`
  then `chmod -R a-w peers/<cell>` (enforce read-only), on a 2–5 min cadence + on demand. `peers/mini` = symlink.
- **B. SSHFS (byte-live, optional):** `sshfs -o ro,reconnect,ServerAliveInterval=15 …` — needs macFUSE; use only
  if byte-liveness is essential.

## How the admin plane reads
| Question | Source | Property |
|---|---|---|
| "What did m1 **publish**?" | `git show origin/cell/m1:<path>` | durable (survives any machine sleeping) |
| "What is m1 **editing now**?" | `peers/m1/<path>` | live-ish (A) / live (B), best-effort |
| "Agreed protocol / ledgers / registry?" | `~/dev/acfr-admin` (admin branch) | curated truth |
Rule: **git = source of truth; `peers/` = live convenience;** if a peer blips, fall back to `origin/cell/<peer>`.

## Reliability
All three peers are reliably up during work, so all three mirrors are first-class. The only real gap is **mini
losing power** — which takes the plane down but loses nothing: `origin` holds all published state; recovery on
boot = `git fetch` + re-sync (+ remount if using B). Self-healing.

## Safety
Peer mirrors are read-only (`-o ro` / `chmod a-w`) — the plane can never mutate another cell's tree. lofra-mini
only curates `admin`, never force-pushes `cell/*`. Fully reversible (`worktree remove` + drop mirrors).

## For lofra-mini — resolve these, then recommend to Col. Raj
You know the specifics; please decide and send Raj your recommendation with rationale:
1. **Current push model** — do cells already push to distinct branches, or migrate from a shared branch to
   `cell/*`? State what's in place today and the migration (if any).
2. **Peer liveness** — rsync mirror (A) vs SSHFS (B). Recommend one; note the cadence for A.
3. **Ledger/registry ownership** — move `INDEX.tsv` / `OUTBOX.tsv` / `PROGRAM-REGISTRY.md` curation onto the
   `admin` branch (recommended), or have the plane only *read* them where they live now?
4. **Machine specifics** — exact ssh user, m1/m4 Tailscale addresses, and each peer's `~/dev/acfr` path
   (note m4's box also runs the dashboard + m4).
5. **Anything the on-the-ground view changes** — if any layer is wrong for how the cells actually operate, say so.

Nothing here is built until Col. Raj approves your recommendations.

— dashboard
