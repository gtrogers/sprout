---
id: verifier
kind: exploded-spec
version: 1
status: active
parent: overview
---

# Verifier

## Purpose

Execute the inventory's verify commands and report honestly which capabilities
actually work. This is the moment the arbiter speaks.

## Responsibilities

- Run the verify command of every `built` row, or one named row
- Report pass or fail per capability, with enough output to debug a failure
- Exit non-zero if any verification fails

## Explicitly not responsible for

- Deciding whether a command is well-formed — that is the Checker
- Running tests directly; it invokes the project's own commands
- Repairing, retrying or interpreting failures

## Interface

### Inputs

| Input | Meaning |
|---|---|
| `verify` | Run every `built` row |
| `verify --id <id>` | Run one row, which must exist and be `built` |

Commands run from the project root with the shell disabled, so a verify command
is a real invocation rather than a shell fragment. This is why single
invocations are required.

### Outputs

| Exit | Meaning |
|---|---|
| 0 | Every executed command passed, or nothing is `built` yet |
| 1 | At least one failed; failures are listed by ID |
| 2 | Cannot run — inventory unreadable, or `--id` names no `built` row |

Each row reports `PASS` or `FAIL` with its command shown. Failures include the
tail of combined output, bounded so one noisy failure cannot bury the others.

### Failure modes

| Condition | Observable result |
|---|---|
| Command exits non-zero | `FAIL` with exit code and output tail |
| Command not found | `FAIL`; not distinguished from a failing check, since both mean unverified |
| Command unparseable | `FAIL` naming the parse problem |
| `built` row with no command | `FAIL`; never silently skipped |
| No `built` rows | Exits 0 with a clear "nothing to verify" |

## Invariants

- Never modifies the project.
- Never reports a capability as verified without running its command and
  observing exit zero.
- `planned` and `building` rows are never executed.
- A failure is always attributed to a specific capability ID.

## Depends on

- Inventory, for rows, statuses and commands.
