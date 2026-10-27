---
id: inventory
kind: exploded-spec
version: 1
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

A markdown table at `INVENTORY.md` in the project root. Markdown, not a data
file, because humans read and edit it far more often than machines do.

| Column | Meaning |
|---|---|
| `ID` | Lowercase-hyphenated, unique across the project |
| `Capability` | What a user can do, in their language |
| `Status` | `planned`, `building` or `built` |
| `Spec` | Path to the spec defining it |
| `Ver` | The spec version it was built against |
| `Verify` | A single command that exits zero when the capability works |

### The verification contract

- `built` requires a non-empty verify command that passes. There is no other
  route to `built`.
- Verify commands are single invocations — no pipes, redirects or chaining — so
  any row can be run by hand. Compound checks live in a script or make target.
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
| Row has wrong cell count | Reported with line number; other rows still checked |

## Invariants

- IDs are unique.
- Every row's spec reference resolves to a real, readable document.
- A row's `Ver` always equals its spec's current version, or the project is in
  a known-failing drift state.

## Depends on

- Document kinds, for the spec references and versions it pins.
