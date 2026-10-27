---
id: inventory
kind: exploded-spec
version: 2
status: active
parent: overview
---

# Inventory

## Purpose

The ledger that decides what exists. It is the arbiter the method is built
around: a capability absent from here, or present without a passing verify
command, does not exist regardless of what the code appears to do.

## Responsibilities

- Record every capability, its state, and how it is verified
- Pin each capability to the spec version it was built against
- Remain readable and editable by hand
- Report progress across states

## Explicitly not responsible for

- Running verify commands — that is the Verifier
- Validating its own contents — that is the Checker
- Scheduling, estimation, assignment or anything else project-management shaped

## Interface

A CSV file at `INVENTORY.csv` in the project root, with a header row.

The ledger is structured data and is stored as such. An earlier version used a
markdown table on the grounds that humans read it more often than machines do,
which conflated reading with storing: the human-facing view is `sprout status`,
which renders better than a raw table ever did.

CSV rather than JSON because the schema is flat with nothing to nest, because
line-oriented storage keeps diffs and branch merges clean, and because stdlib
quoting removes the hand-editing traps that punctuation in a capability
description would otherwise create.

| Column | Meaning |
|---|---|
| `id` | Lowercase-hyphenated, unique across the project |
| `capability` | What a user can do, in their language |
| `slice` | The slice delivering it; must name a real slice document |
| `status` | `planned`, `building` or `built` |
| `spec` | Path to the spec defining it |
| `ver` | The spec version it was built against |
| `verify` | A single command that exits zero when the capability works |

The `slice` column links capabilities to the work that delivers them. Without
it, "all of this slice's rows are built" cannot be computed and slice state has
to be declared by hand — a self-reported claim of exactly the kind this ledger
exists to refuse.

### The verification contract

- `built` requires a non-empty verify command that passes. There is no other
  route to `built`.
- Verify commands are single invocations — no pipes, redirects or chaining — so
  any row can be run by hand. Compound checks live in a script or make target.
  CSV quoting would now tolerate a pipe, so this is a deliberate rule rather
  than a storage constraint: it keeps every row independently runnable.
- `planned` and `building` rows may omit the command, but a `planned` row whose
  command cannot be *named* signals work that is not yet understood.

### State transitions

`planned` → `building` when work starts → `built` when verification passes.
`built` → `building` when a re-verification fails. The backwards transition is
required, not optional: a regression means the capability has stopped existing.

### Failure modes

| Condition | Observable result |
|---|---|
| File absent | Checker and Verifier both report it and fail |
| Missing required column | Reported with the column names; parsing stops |
| Row has wrong field count | Reported with line number; other rows still checked |
| Unparseable CSV | Reported with line number and the parse error |

## Invariants

- IDs are unique.
- Every row's spec reference resolves to a real, readable document.
- Every row's slice reference resolves to a real slice document.
- A row's `Ver` always equals its spec's current version, or the project is in
  a known-failing drift state.

## Depends on

- Document kinds, for the spec references and versions it pins.
