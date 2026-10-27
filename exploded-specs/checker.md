---
id: checker
kind: exploded-spec
version: 4
status: active
parent: overview
---

# Checker

## Purpose

Validate specs, inventory and skills deterministically, and detect drift
between a spec's version and the rows pinned to it. This is what makes the
method's rules enforceable rather than aspirational.

## Responsibilities

- Validate every document's frontmatter against the contract
- Validate the inventory table's structure and every row
- Detect version drift between specs and the rows pinned to them
- Validate shipped skills against the Agent Skills standard
- Report every problem found, not just the first

## Explicitly not responsible for

- Executing verify commands — that is the Verifier
- Judging whether a spec is at the right altitude, or whether its content is
  any good
- Fixing anything; the Checker only reports

## Interface

`check` takes no arguments and inspects the whole project.

### Outputs

| Exit | Meaning |
|---|---|
| 0 | Every rule holds; a summary line states what was checked |
| 1 | One or more problems; each printed with its file and line |
| 2 | Cannot run — no `.sprout/` found |

Problems are reported with enough location to act on without searching, and
every problem is printed in one pass so a single run gives the full picture.

### Rules enforced

Specs: frontmatter present and terminated; `id`, `kind`, `version`, `status`
present; `kind` is known; `status` is valid **for that kind**; `id` matches
filename; `version` is a positive integer.

Validating `status` against the kind closes a gap in v1, which checked only
that the field was present. A slice could therefore carry any value at all,
and one did — undetected — until the Navigator needed to read the lifecycle.

Inventory: CSV parses with all required columns; subsystem ids unique and
well-formed; every row's spec exists and its `id` matches the row; `implemented`
is blank or a positive integer no greater than the spec's current version;
`status` known; spec reference resolves; `Ver` matches the spec's current
version; `built` rows carry a verify command; verify commands are free of shell
metacharacters.

Skills: exactly one file named `SKILL.md` per directory, in that exact case;
`name` and `description` both present; `name` matches its directory;
description within 1024 characters. Over-long skills are a warning, not a
failure, since length is guidance rather than a rule.

### Failure modes

| Condition | Observable result |
|---|---|
| Spec version bumped past `implemented` | Not a failure. The gap is work owed and the Navigator reports it |
| `implemented` above the spec's version | Failure, naming both versions |
| Unreadable document | Reported as unreadable; the run continues |
| Inventory absent | Reported; spec checks still run |

## Invariants

- Pure: reports and changes nothing.
- Deterministic: same inputs, same output, no network or clock dependence.
- Never passes a project whose implemented rows lack verify commands.
- Never fails a project merely because a spec has evolved ahead of its
  implementation. That is the normal mid-slice state.
- Warnings never affect the exit code.

## Depends on

- Document kinds, for the frontmatter contract.
- Inventory, for the table contract and the verification rule.
