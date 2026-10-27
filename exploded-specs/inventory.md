---
id: inventory
kind: exploded-spec
version: 3
status: active
parent: overview
---

# Inventory

## Purpose

The ledger of subsystem evolution. Subsystem specs grow and change as the
project is built up slice by slice; this records, for each subsystem, which
spec version the implementation currently satisfies and how that is checked.

The gap between a spec's version and the version implemented is **work owed**.
It is the queue the project works through, not a fault.

## Responsibilities

- Record every subsystem, its spec, the version implemented, and its check
- Make the spec-to-implementation gap visible and computable
- Remain readable and editable by hand

## Explicitly not responsible for

- Listing capabilities or features. A slice document says what is being
  delivered; this says what state each subsystem is in.
- Running verify commands — that is the Verifier
- Validating its own contents — that is the Checker
- Scheduling, estimation, assignment or anything project-management shaped

## Interface

A CSV file at `INVENTORY.csv` in the project root, with a header row. One row
per subsystem.

| Column | Meaning |
|---|---|
| `subsystem` | Lowercase-hyphenated id, matching its exploded spec's `id` |
| `spec` | Path to the exploded spec defining it |
| `implemented` | The spec version the implementation satisfies; empty if none |
| `verify` | A single command that exits zero when the subsystem meets its spec |

The spec's *current* version is deliberately not stored. It is read from the
spec file, so it cannot go stale — only one number is recorded here, and it is
the one a machine cannot derive: what the implementation actually satisfies.

### Derived state

| Condition | State |
|---|---|
| `implemented` empty | `planned` — specced, nothing built |
| `implemented` < spec version | `building` — the spec has evolved past the code |
| `implemented` == spec version | `built` |
| `implemented` > spec version | inconsistent; fails the checks |

A subsystem is only `built` when its verify command passes at the spec's
current version. Bumping `implemented` without re-verifying is the one move
that breaks the ledger's meaning.

### The verification contract

- Verify commands are single invocations — no pipes, redirects or chaining — so
  any row can be run by hand. Compound checks live in a script or make target.
- A subsystem with no verify command can never be more than `planned`.

### Failure modes

| Condition | Observable result |
|---|---|
| File absent | Checker and Verifier both report it and fail |
| Missing required column | Reported with the column names; parsing stops |
| Row has wrong field count | Reported with line number; other rows still checked |
| Unparseable CSV | Reported with line number and the parse error |
| `implemented` above the spec's version | Reported as an inconsistency |

## Invariants

- Subsystem ids are unique, and each names a real exploded spec whose `id`
  matches.
- Every exploded spec has exactly one row. A specced subsystem absent from the
  ledger would be work owed that nothing reports, so the gap set stays a
  complete description of outstanding work.
- `implemented` never exceeds its spec's current version.
- A gap is not a failure. Consistency is checked; progress is reported.

## Depends on

- Document kinds, for the exploded specs it references and their versions.
