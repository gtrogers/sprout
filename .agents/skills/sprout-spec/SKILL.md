---
name: sprout-spec
description: Write or revise a project's high-level overview spec, covering goals, intent, subsystems, constraints and invariants. Use when starting a new project, when the user asks for a spec or to set up sprout, or when the shape of the project has changed enough that the overview spec is now wrong.
---

# Overview spec

One document per project describing what it is for and what must hold. Every
exploded spec is derived from it.

## Invariant

The spec states goals and intent, never implementation.

The test: if a competent developer could build this three different ways and
all three would satisfy the user, the altitude is right. If the spec is one
implementation written in prose, it is too low — raise it.

Belongs: the problem and whose it is; goals as outcomes; non-goals as explicit
exclusions; named subsystems with one-line purposes; constraints that are
*given* rather than chosen; invariants that hold at every commit.

Does not belong: signatures, schemas, file layouts, algorithms, library choices
that are not constraints, or anything a test could pin down.

## Enter when

- The user wants a new project specced, or the overview spec is now wrong.
- If `.sprout/sprout.py` is absent this project is not initialised. Ask whether
  to set it up; if yes, copy `.sprout/` and `.agents/skills/` from the sprout
  repo, create `INVENTORY.csv` from `.sprout/templates/INVENTORY.csv`, and append
  `.sprout/templates/AGENTS-block.md` to `AGENTS.md`.

Scaffold with `python3 .sprout/sprout.py new spec overview`.

## Loop

Each pass: ask about one area, draft it, read it back, let the user correct it.
Do not interview everything then write everything — you will encode your own
assumptions and the user will not see them until too late.

Work the areas in this order, highest value per question first:

1. **Non-goals.** What this explicitly will not do. Users rarely volunteer
   this; it prevents more rework than any other section.
2. **Invariants.** What must never break. Push for properties that could
   actually be checked, since these become real checks later.
3. **Constraints.** Separate genuinely given from merely assumed: "is that
   fixed, or just the first thing that came to mind?"
4. **Subsystems.** Aim for 3–7. More means the boundaries are wrong — look for
   a missing layer of grouping.
5. **Problem and goals.** Easiest to state, so write them last, once the
   preceding answers have sharpened them.

Record real uncertainty under Open questions. Never resolve an unknown with a
plausible-sounding guess; a guess in a spec is indistinguishable from a
decision once it is written down.

Each pass, re-ask: has anything learned invalidated an earlier section?

### Revising an existing spec

Bump `version` on every substantive change, then run
`python3 .sprout/sprout.py next`. Any subsystem now behind its spec is reported
as work owed — the checks still pass, because a spec ahead of its code is the
normal state mid-slice. That gap is the queue.

Never raise a subsystem's `implemented` version without re-verifying it. It is
the one number in the project that cannot be derived, which is exactly why it
may only be changed on evidence.

## Exit — success

- `specs/overview.md` has complete frontmatter
- Non-goals and invariants are both non-empty
- Subsystems are named with purposes
- `python3 .sprout/sprout.py check` passes
- The user confirms it describes what they want built

Then: `sprout-slice`.

## Exit — failure

Stop and route, rather than writing a spec that looks finished but is not:

- **Scope keeps growing each pass.** Three passes without the non-goals
  stabilising means this is more than one project. Propose splitting it, and
  spec the first part only.
- **An unknown blocks the shape.** If the answer to "which subsystems exist"
  depends on a technical unknown, stop and run `sprout-spike` on that question.
  A spec built on a guessed technical premise is worse than no spec.
- **The user cannot articulate goals yet.** Recommend a throwaway prototype to
  find them. Say plainly that specs cannot manufacture intent.
