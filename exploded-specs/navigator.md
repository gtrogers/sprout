---
id: navigator
kind: exploded-spec
version: 4
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
- Deciding *which* subsystem to work on when several lag. It reports them; the
  order is a judgement for the build loop.

## Interface

### Inputs

`next` takes no arguments. Everything it reports is derived from `specs/`,
`exploded-specs/`, `slices/`, `INVENTORY.csv`, and the Checker's result.

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
| 2 | Any subsystem's `implemented` lags its spec version | `sprout-build` |
| 3 | Overview spec exists, no gaps remain | `sprout-slice` |
| 4 | No overview spec | `sprout-spec` |

Four rules, because the flow is one-way. A slice does not declare which
subsystems it touches: updating an exploded spec *is* that declaration, and the
resulting gap is what the Navigator reads. Declaring it again in the slice
document would be duplicate bookkeeping with its own way of going stale.

Work owed is therefore global rather than per-slice, which is sound because
sprout runs one slice at a time. "No gaps remain" means the current slice is
delivered.

Rule 1 outranks everything because a project that cannot be parsed has no
trustworthy position, and it yields the pseudo-loop `repair` rather than a
skill name.

There is no longer a drift rule. A spec ahead of its implementation is the
normal mid-slice state, not a fault: it is rule 2, and it routes to the build
loop rather than to repair.

**Nothing the Navigator reads is self-reported.** Spec versions come from the
spec files; implemented versions come from the ledger and may only be raised by
re-verifying. There is no field anyone can set to claim progress.

**There is no showcase rule.** Showcasing is an action, not a state, and a flag
asserting it had happened would be unverifiable. Rule 6 prompts for it in its
action text instead. This is the one loop the Navigator cannot route to on
evidence, and it is a known gap rather than an oversight.

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
- Document kinds, for the document contract.
- Inventory, for each subsystem's implemented version.

## Open questions

- Sub-loop position inside `sprout-build` is not derivable from artifacts. The
  observation log would supply it; until that exists, `next` reports the loop
  coarsely and says so rather than guessing.
- Should a spike with an unanswered question block its dependent loop? It would
  need a machine-readable link from spike to blocked decision, which may be
  more bookkeeping than it earns.
- Showcase cannot be routed to on evidence until showcase events are recorded.
  Once the observation log exists, "no showcase recorded for this built slice"
  becomes a detectable gap and the rule can return — grounded in something that
  happened rather than a flag someone set.
