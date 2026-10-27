# Sprout

A lightweight, cross-agent framework for spec-driven, slice-based delivery.

Specs describe intent. Tests pin down behaviour. An inventory decides what
exists. One command settles whether the work you were promised is real.

> **If a subsystem cannot be verified deterministically and programmatically,
> it is not implemented.**

Sprout is specced, sliced and verified with its own method, so this repository
is also a worked example. Six skills, one ~450-line stdlib Python tool, four
document kinds. No dependencies, no service, no personas.

## Install

```sh
git clone <this repo> sprout
python3 sprout/install.py /path/to/your/project
```

That copies the tooling and skills in, wires up every agent's discovery path,
and appends the invariants to `AGENTS.md`. Re-running is safe; `--force`
upgrades the method without ever touching your specs.

Then start the `sprout-spec` skill, or ask your agent to "spec out this project
with sprout".

## The loops

Six skills, one per loop. Each names its entry conditions, its success exit,
and — the part that matters — its **failure exits**, so an agent that is stuck
recognises it and routes instead of thrashing.

| Skill | Loop | Fails out to |
|---|---|---|
| `sprout-spec` | Interview and draft until the overview spec is agreed | spike, or split the project |
| `sprout-slice` | Shape a deliverable slice, explode each subsystem it touches | spec, spike, or re-slice |
| `sprout-build` | Drive tests to *predicted* failure, then to green | spike, or fix the spec |
| `sprout-tidy` | Fold learnings back, bump versions, re-pin the inventory | spec |
| `sprout-showcase` | Produce usable proof, then loop on feedback | build, spec, or re-slice |
| `sprout-spike` | Investigate one question under a timebox, distil to a page | split the question |

The loop that does the most work is `sprout-build`. It writes black-box tests
first, then **predicts how each will fail** and checks the prediction before
writing any implementation. A test that passes early, or fails for the wrong
reason, is a finding — not a green light.

## The documents

| Kind | Altitude |
|---|---|
| `specs/overview.md` | Project goals and intent. Subsystems named, not designed |
| `exploded-specs/*.md` | One subsystem's intent and interface, scoped to a slice |
| `slices/*.md` | One valuable, end-to-end, deliverable piece of work |
| `spikes/*.md` | One timeboxed question, distilled to a single page |

All four obey one rule: **anything a test could pin down belongs in a test**,
not in a document. Specs say what callers may rely on; tests say exactly what
happens.

Every document carries a monotonic `version` in YAML frontmatter — except a
slice, which declares neither a version-bearing status nor the subsystems it
touches. Both are derived: updating an exploded spec *is* how a slice declares
it will touch that subsystem, and the resulting gap is what `sprout next`
reads.

The flow is strictly one-way, and specs move first:

    overview spec -> exploded specs -> tests -> implementation -> tidy

## The inventory

`INVENTORY.csv` is the arbiter — a ledger of **subsystem evolution**. Subsystem
specs grow as a project is built up; this records, for each one, which spec
version the implementation satisfies and how that is checked.

```csv
subsystem,spec,implemented,verify
auth,exploded-specs/auth.md,2,make verify-auth
```

The spec's *current* version is deliberately not stored — it is read from the
spec file, so it cannot go stale. Only one number lives here, and it is the one
a machine cannot derive: what the code actually satisfies.

**The gap is the work.** A spec ahead of its implementation is not an error, it
is the queue:

| Condition | State |
|---|---|
| `implemented` empty | `planned` |
| `implemented` < spec version | `building` — work owed |
| `implemented` == spec version | `built` |
| `implemented` > spec version | inconsistent; fails the checks |

Raising `implemented` without re-verifying is the one move that destroys the
ledger's meaning, which is why nothing but a passing verify command should ever
raise it. Revise that spec
and every row pinned to it **drifts**, failing checks until each is re-verified
and re-pinned. That is the mechanism that stops specs quietly becoming fiction.

## Commands

```sh
python3 .sprout/sprout.py next             # which loop am I in, and what is blocking it
python3 .sprout/sprout.py check            # specs versioned, inventory consistent, no drift
python3 .sprout/sprout.py verify           # run every built capability's command
python3 .sprout/sprout.py verify --id X    # run one
python3 .sprout/sprout.py status           # what is built, building, planned
python3 .sprout/sprout.py new slice X      # scaffold from a template
```

### Where am I?

Projects stall when the state lives in a context window that is gone. `next`
reconstructs it from the artifacts alone, by a fixed precedence, so a fresh
session — or a different agent — resumes without re-deriving anything:

```
rule     5
loop     sprout-build
reason   slice 'slice-state-is-derived' is specced with 3 capability(ies) planned
blocker  3 capability(ies) still planned
action   Write the black-box tests for the slice walkthrough, then confirm
         each fails in the code under test before implementing.
```

Structural failures outrank everything (an unparseable project has no
trustworthy position) and drift outranks progress (building on a drifted spec
is how specs become fiction). `--json` emits the same position for an agent to
consume.

`next`, `check` and `verify` are pure — they report and change nothing. Both are
suitable as a CI gate and as the bar an agent must clear before claiming
anything is done.

## Cross-agent support

Skills follow the Agent Skills open standard, deliberately using only `name` and `description` frontmatter — every other
field in the standard is honoured by some agents and silently stripped by
others.

Skills live canonically in `.agents/skills/`, the widest-read discovery path
(Codex CLI, Cursor, Gemini CLI). `install.py` links `.claude/skills`,
`.cursor/skills` and `.gemini/skills` to it, falling back to copies where
symlinks are unavailable. Portability is enforced by a check, not a promise:

```sh
python3 verify/verify.py skills-are-cross-agent-portable
```

The division that keeps this lightweight: **`AGENTS.md` carries the always-on
invariants; skills carry the on-demand procedure.** You don't pay context for
the whole method on every turn — around 25 lines of non-negotiables stay
resident, and the loop bodies load only when a loop starts.

## Verifying sprout itself

```sh
python3 verify/verify.py --all
```

Black-box tests that drive the CLI as a subprocess in throwaway projects,
grouped by subsystem — the unit the ledger tracks, so each row's verify command
asks "does this subsystem meet its spec". None of them import the tool.

```sh
python3 verify/verify.py navigator    # one subsystem
python3 verify/verify.py --list
```
