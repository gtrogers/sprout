---
id: skills
kind: exploded-spec
version: 1
status: active
parent: overview
---

# Skills

## Purpose

The loops an agent follows, expressed as portable `SKILL.md` files that any
conforming agent can discover and activate.

## Responsibilities

- Encode each loop of the method as one skill
- Give every loop explicit success and failure exits
- Stay within the portable subset of the Agent Skills standard

## Explicitly not responsible for

- Holding project state; skills are procedure, the project holds the facts
- Enforcing anything — enforcement is the Checker's and Verifier's job
- Agent-specific behaviour or configuration

## Interface

Six skills, one per loop:

| Skill | Loop |
|---|---|
| `sprout-spec` | Interview and draft until the overview spec is agreed |
| `sprout-slice` | Shape a slice, then explode each subsystem it touches |
| `sprout-build` | Drive tests to predicted failure, then to green |
| `sprout-tidy` | Fold learnings back, bump versions, re-pin the inventory |
| `sprout-showcase` | Produce usable proof, then loop on feedback |
| `sprout-spike` | Investigate one question under a timebox, then distil |

### Structure of a skill

Each states, in this order: its **invariant**, its **entry conditions** with
routing when unmet, its **loop body**, its **success exit**, and its
**failure exits** — each naming where to go instead.

Failure exits are the part that distinguishes these from phase descriptions. A
loop that cannot state how it fails gives an agent no way to recognise
thrashing, and an agent that cannot recognise thrashing lowers the bar instead.
Where a loop could run indefinitely, it carries an explicit budget — typically
two or three passes — after which not-converging is itself the outcome.

### Portability contract

- Frontmatter is `name` and `description` only. Every other standard field is
  honoured by some agents and stripped by others, so using one trades
  portability for power the method does not need.
- The file is named exactly `SKILL.md`; other spellings are silently ignored on
  case-sensitive filesystems.
- `name` matches the containing directory.
- `description` opens with an action verb and states a trigger condition, since
  agents activate on semantic relevance to that text alone.

### Failure modes

| Condition | Observable result |
|---|---|
| Wrong filename case | `check` fails, explaining the case-sensitivity trap |
| `name` mismatched to directory | `check` fails |
| Non-portable frontmatter field | Portability verification fails |
| Over 500 lines | `check` warns; move detail into `references/` |

## Invariants

- Every skill names at least one failure exit with a destination.
- No skill depends on an agent-specific feature.
- Skills are stateless; re-entering one mid-project is always safe.

## Depends on

- Checker, for portability enforcement.
