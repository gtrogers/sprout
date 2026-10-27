---
id: distribution
kind: exploded-spec
version: 3
status: active
parent: overview
---

# Distribution

## Purpose

Get sprout into a project and wire up every agent's entry point, so one method
is followed regardless of which agent is driving.

## Responsibilities

- Copy the tooling and skills into a target project
- Wire each agent's skill discovery path to one canonical location
- Create the project's starting state without overwriting existing work
- Support upgrading the method in a project already using it

## Explicitly not responsible for

- Installing language runtimes or project dependencies
- Version-controlling anything; the user commits what they want
- Removing itself

## Interface

### Inputs

| Input | Meaning |
|---|---|
| `install.py <target>` | Install into the target directory, creating it if needed |
| `--force` | Replace tooling and skills with newer versions |

### What lands in the project

| Path | Role |
|---|---|
| `.sprout/` | Tool and templates, committed with the project |
| `.agents/skills/` | Canonical skills; the widest-read discovery path |
| `.claude/skills`, `.cursor/skills`, `.gemini/skills` | Links to the canonical location |
| `INVENTORY.csv` | The subsystem ledger, header only but valid |
| `AGENTS.md` | Always-on invariants appended; `CLAUDE.md` points at it |
| `specs/`, `exploded-specs/`, `slices/`, `spikes/`, `verify/` | Where documents and checks live |

Agents read skills from different paths, so one canonical directory plus links
is the only arrangement that works everywhere. Where symlinks are unavailable,
a copy is made and the substitution is reported rather than hidden.

The always-on invariants go in `AGENTS.md` and the method bodies stay in
skills, so a project does not pay context for the whole method on every turn.

### Failure modes

| Condition | Observable result |
|---|---|
| Target is the sprout repo | Exits 2; refuses |
| Tooling already present, no `--force` | Skipped, with a line saying `--force` would update |
| `AGENTS.md` already has the block | Skipped; never duplicated |
| Symlinks unavailable | Falls back to copying and says so |
| Existing `INVENTORY.csv`, specs or `CLAUDE.md` | Always left untouched, `--force` included |

## Invariants

- Re-running is safe and idempotent.
- Project state — specs, slices, spikes, inventory — is never overwritten, even
  with `--force`.
- After install, `check` passes and `status` runs on the empty project.
- Every wired path resolves to the same skills.

## Depends on

- Skills, for what is distributed.
- Document kinds, for the directory layout and templates.
