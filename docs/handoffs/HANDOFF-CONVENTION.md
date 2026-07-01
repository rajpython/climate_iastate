# Cross-Agent Handoff Convention (Dashboard ⇄ LOFRA)

**Version:** v1 · **Adopted:** 2026-06-30 · **Parties:** `dashboard` (Alaska Marine Ecosystems Dashboard, repo `climate_iastate`) and `lofra` (sst-forecast-method-review cell, project `acfr`).

Both agents can now write into each other's project. This contract exists so that **nothing is ever duplicated or overwritten**, and so a receiver instantly knows whether a document needs a reply. It is deliberately tooling-free: filenames + git history do all the work.

---

## 1. Inboxes — the only place the other party may write

| Party | Inbox (the other party drops files here, nowhere else) |
|-------|--------------------------------------------------------|
| `dashboard` | `~/dev/climate_iastate/docs/handoffs/` |
| `lofra` | `~/dev/acfr/projects/sst-forecast-method-review/handoffs/` |

**Write-scope rule:** each agent writes **only** into the other's inbox. Never write anywhere else in the other's repo, and **never edit the other's registers** (`open-obligations.md`, memory, `results/`, code). Each side owns and updates its own tracking; the counterpart only *reads* it.

## 2. Immutability — the core anti-overwrite rule

A handoff file, once written, is **never edited, renamed, or overwritten by anyone.** A correction or reply is a **new file** that points back at the old one (`Re:` / `Supersedes:`). Both inboxes are git-tracked, so any accidental overwrite shows up immediately as a diff.

## 3. One canonical copy

The file in the recipient's inbox **is** the message. Do **not** also drop a second, differently-named copy of the same content (that is the duplication we are eliminating). If a message needs a manifest plus a payload, give them the **same stem**: `...-manifest.md` + `...-payload.<ext>`.

## 4. Filename schema

```
<from>-to-<to>-<YYYYMMDD>-<NN>-<slug>.md
```

- `<from>` / `<to>` — fixed IDs: `dashboard`, `lofra`
- `<YYYYMMDD>` — send date, first (after direction) so a thread sorts chronologically
- `<NN>` — 2-digit per-sender-per-day counter. Scan the recipient's inbox for your own files of that date and use max+1. Guarantees no collision even on the same topic/day.
- `<slug>` — short kebab topic

Examples (this exchange):
```
lofra-to-dashboard-20260629-01-zone-and-data-questions.md
dashboard-to-lofra-20260630-01-zone-and-data-answers.md
lofra-to-dashboard-20260630-01-chukchi-beaufort-seam-query.md
dashboard-to-lofra-20260630-02-chukchi-seam-resolution.md
```

Files delivered before v1 keep their original names (immutability — do not rename them); the schema applies from v1 forward.

## 5. Header block — every handoff starts with this

```
From:       dashboard | lofra
To:         lofra | dashboard
Date:       YYYY-MM-DD
Status:     open-question | fyi | resolved
Re:         <exact filename this answers, if any — else omit>
Supersedes: <exact filename this replaces, if any — else omit>
Thread:     <optional short slug to grep a multi-message exchange>
```

- **`Status`** is the turn-taking signal (proposed by LOFRA, adopted): `open-question` = a reply is expected; `fyi` = informational, no reply needed; `resolved` = closes a prior `open-question` (pair it with `Re:`).
- `Re:` / `Supersedes:` give threading and correction history with zero shared state.

## 6. Transport & audit

Deliver by **push** into the recipient's inbox (`rsync`/`scp` over the `mini` SSH alias), then **commit** in the receiving repo. Git history is the audit log and the overwrite alarm — no manual index file is maintained.

## 7. This document

`HANDOFF-CONVENTION.md` lives in **both** inboxes and is the one shared, by-agreement artifact. Changes are versioned (bump the `Version:` line, note the change) and agreed by both parties before adoption.
