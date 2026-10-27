---
name: sprout-slice
description: Define a deliverable end-to-end slice of work, update the overview spec if its goals or constraints change, and explode it into per-subsystem specs. Use when planning what to build next, when the user asks to spec out or plan a slice or feature, or before starting implementation on anything non-trivial.
---

# Slice and explode

A slice is a valuable, end-to-end, deliverable piece of work. Exploding is
deriving one spec per touched subsystem, scoped to that slice. They are one
activity: a slice you cannot explode is not yet understood.

## Invariant

Specs move first, and only forward. The flow is one-way:

    overview spec -> exploded specs -> tests -> implementation -> tidy

Updating an exploded spec is how a slice declares it will touch that subsystem.
Do not also list the subsystems in the slice document: the resulting gap
between a spec's version and the version implemented is what `sprout next`
reads, and a second declaration is bookkeeping that can go stale.

Every subsystem this slice advances needs a verify command in the ledger
*before* implementation starts. Deciding verification while the work can still
be shaped around being verifiable is the highest-leverage moment in the method.

## Enter when

- The overview spec exists and `sprout check` passes. If not: `sprout-spec`.
- The user wants to plan the next piece of work.

Scaffold with `python3 .sprout/sprout.py new slice <name>`.

## Gate — does this change the overview spec?

Ask before touching any exploded spec, because getting this wrong leaves the
overview lying and nothing will catch it:

- Does it change a **goal** or add a **non-goal**?
- Does it contradict a stated **constraint** or **invariant**?
- Does it need a **subsystem the overview does not name**?

Any yes: stop and run `sprout-spec` first, bumping the overview's version.
Deferring this to the tidy pass is the most common way a project ends up with
a confident, false overview spec.

## Loop A — shape the slice

The bar: **it can be shown to someone and understood without explanation.**
"Add a users table" fails — nothing is observable. "A new user can sign up and
see their empty dashboard" passes.

Each pass, draft these and test them against the bar:

- **Value.** What a user can do that they could not before. One sentence, their
  language, not the system's.
- **Walkthrough.** The end-to-end path as observable steps. This becomes the
  skeleton of the black-box tests, so vagueness here becomes untestable work.
- **Verification.** Each subsystem this slice advances must have a verify
  command in `INVENTORY.csv` before implementation begins. Single invocations
  only — no pipes or redirects; wrap anything compound in a script under
  `verify/` or a make target, so a human can run it by hand.
- **Showcase.** How it gets demonstrated. If the answer is "the tests pass",
  there is no showcase yet — keep going.

Exit this loop when every subsystem the slice advances has a verify command
you could run today if the code existed. If you cannot name one, the work is
either not well defined or does not belong in this slice. Both are findings —
act on them rather than writing `TODO`.

## Loop B — explode each subsystem

For each subsystem the slice touches:

    python3 .sprout/sprout.py new exploded-spec <subsystem>

Describe **intent and interface**, scoped to what this slice needs — not a
complete future design. If a subsystem already has a spec, revise it in place
and bump `version`; never create a parallel document.

Bumping the version is what puts the work on the queue: the spec is now ahead
of the code, `sprout check` still passes, and `sprout next` routes to the build
loop naming that subsystem. Scaffolding a new exploded spec also adds its
ledger row, which starts unimplemented with no verify command — fill the
command in now.

The discipline: anything a unit or end-to-end test could pin down belongs in a
test, not here. Specs say what callers may rely on; tests say exactly what
happens. Ask "could I write a test that proves this?" If yes, write the test
instead.

Do not omit **failure modes**. Callers depend on failure behaviour as much as
success behaviour, so it is part of the interface. For each condition, state
what the caller observes.

Exit this loop when every touched subsystem has a current spec whose interface
covers every walkthrough step, failure modes included.

## Then confirm the queue

    python3 .sprout/sprout.py check
    python3 .sprout/sprout.py next

`check` must pass — a spec ahead of its implementation is not a failure. `next`
must route to the build loop and name the subsystems now owed work. If it does
not, the specs did not actually move.

## Exit — success

- The overview spec is true, and was updated first if the gate demanded it
- Slice doc has value, a walkthrough and a real showcase
- Every advanced subsystem has a current exploded spec with failure modes
- Every advanced subsystem has a verify command in the ledger
- `sprout check` passes and `sprout next` names the work owed

Then: `sprout-build`.

## Exit — failure

- **Too big.** Walkthrough beyond ~7 steps, or more than 3 subsystems touched.
  Split it and spec the first part only. Do not proceed hoping it shrinks.
- **Not showable.** If no showcase can be described, this is a task, not a
  slice. Either fold it into a slice that is showable, or get explicit
  agreement from the user that you are building something unshowable and why.
- **The gate says yes.** The slice changes a goal, contradicts a constraint or
  invariant, or needs a subsystem the overview does not name. Stop; go to
  `sprout-spec` and update the overview first. Never carry on intending to fix
  the overview later.
- **A subsystem resists verification.** After two passes you still cannot name
  a verify command. Say so explicitly. Usually the intent is really a quality
  ("it feels fast") that needs restating as something measurable, or it needs a
  spike to discover how to observe it.
- **An unknown blocks the interface.** You cannot state a subsystem's interface
  without knowing something you do not know. Run `sprout-spike` on it.
