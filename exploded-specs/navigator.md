---
id: navigator
kind: exploded-spec
version: 2
status: active
parent: overview
---

# Navigator

## Purpose

Answer "where am I and what is next" from the project's artifacts alone, so a
fresh session — or a fresh agent — can resume without re-deriving state that
lived in a context window and is now gone.

This is where projects stall: not because the method is unclear, but because
nobody can cheaply establish which loop they are in.

## Responsibilities

- Determine the current loop from artifacts on disk
- Name what is blocking the transition out of it
- State the single next action
- Resolve ambiguity by a fixed, published precedence

## Explicitly not responsible for

- Invoking agents, or doing the work it names. It reports a position; it never
  drives.
- Validating specs or the inventory — that is the Checker. The Navigator
  consumes the Checker's verdict.
- Tracking sub-loop position inside `sprout-build` (Loop A versus Loop B).
  Test results are not artifacts, so this is outside what can be derived. See
  Open questions.

## Interface

### Inputs

`next` takes no arguments. Everything it reports is derived from `specs/`,
`exploded-specs/`, `slices/`, `INVENTORY.md`, and the Checker's result.

### Outputs

For the resolved position: the **loop** to enter, the **reason** that position
was chosen, the **blocker** preventing the next transition, and the **action**
to take. Human-readable by default; `--json` for machine consumption.

| Exit | Meaning |
|---|---|
| 0 | A position was determined |
| 2 | Cannot determine — project unreadable or not initialised |

Exit status reports whether a position could be *found*, never whether the
project is healthy. A project in a failing state still has a well-defined
position, and that is the most valuable moment to ask.

### Precedence

Evaluated top-down; the first matching rule wins. Published, fixed, and
deterministic, so two agents on the same artifacts always get the same answer.

| # | Condition | Loop |
|---|---|---|
| 1 | Structural check failures (frontmatter, malformed inventory) | `repair` — not a skill |
| 2 | Any drifted row | `sprout-tidy` |
| 3 | Any row `building` | `sprout-build` |
| 4 | A slice's status is `built` (not yet `showcased`) | `sprout-showcase` |
| 5 | Slice in flight, a touched subsystem has no current exploded spec | `sprout-slice` |
| 6 | Slice in flight with rows `planned`, none `building` | `sprout-build` |
| 7 | Overview spec exists, no slice in flight | `sprout-slice` |
| 8 | No overview spec | `sprout-spec` |

Rule 1 outranks everything because a project that cannot be parsed has no
trustworthy position, and it yields the pseudo-loop `repair` rather than a
skill name. Rule 2 outranks progress because building on a drifted spec is how
specs become fiction. Rule 3 outranks rule 4 so that a capability in progress
is never masked by a slice awaiting showcase.

**Slice status is maintained, not derived.** Inventory rows reference specs,
not slices, so there is no link from a slice to the capabilities it delivers
and "all of this slice's rows are built" cannot be computed. Rules 4 to 7 read
the slice document's own `status`. That status is still an artifact — written
down, versioned and reviewable — rather than an agent's in-context claim, and
capability-level truth remains wholly derived from the inventory. But it can
disagree with the rows, and nothing currently detects that.

### Failure modes

| Condition | Observable result |
|---|---|
| Not initialised | Exits 2, says how to install |
| Empty project | Rule 8; names `sprout-spec` rather than erroring |
| Inventory unparseable | Rule 1; reports the parse failure as the blocker |
| Multiple slices in flight | Reports each with its own position; never guesses which is intended |

## Invariants

- Pure: reports and changes nothing.
- Deterministic: same artifacts, same answer, with no dependence on clock,
  network or history.
- Always returns a position for a readable project; "nothing to do" is itself a
  position, not an error.
- Never reports a loop whose entry conditions are unmet.

## Depends on

- Checker, for the verdict that rules 1 and 2 consume.
- Document kinds, for the slice lifecycle that rules 4 to 7 read.
- Inventory, for row statuses.

## Open questions

- Sub-loop position inside `sprout-build` is not derivable from artifacts. The
  observation log would supply it; until that exists, `next` reports the loop
  coarsely and says so rather than guessing.
- Should a spike with an unanswered question block its dependent loop? It would
  need a machine-readable link from spike to blocked decision, which may be
  more bookkeeping than it earns.
- Should the inventory gain a `Slice` column, so slice status becomes derived
  rather than maintained? It would close the disagreement described above and
  let the Checker catch a slice claiming `built` while its rows are `planned`.
  The cost is a schema change to the one file users edit most by hand.
