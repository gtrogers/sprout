---
name: sprout-slice
description: Define a deliverable end-to-end slice of work and explode the overview spec into per-subsystem specs for it. Use when planning what to build next, when the user asks to spec out or plan a slice or feature, or before starting implementation on anything non-trivial.
---

# Slice and explode

A slice is a valuable, end-to-end, deliverable piece of work. Exploding is
deriving one spec per touched subsystem, scoped to that slice. They are one
activity: a slice you cannot explode is not yet understood.

## Invariant

Every capability in the slice has a named verify command *before* implementation
starts. Deciding verification while the work can still be shaped around being
verifiable is the single highest-leverage moment in the method.

Verify commands are single invocations — no pipes or redirects. Wrap anything
compound in a script under `verify/` or a make target, so a human can run it by
hand too.

## Enter when

- The overview spec exists and `sprout check` passes. If not: `sprout-spec`.
- The user wants to plan the next piece of work.

Scaffold with `python3 .sprout/sprout.py new slice <name>`.

## Loop A — shape the slice

The bar: **it can be shown to someone and understood without explanation.**
"Add a users table" fails — nothing is observable. "A new user can sign up and
see their empty dashboard" passes.

Each pass, draft these and test them against the bar:

- **Value.** What a user can do that they could not before. One sentence, their
  language, not the system's.
- **Walkthrough.** The end-to-end path as observable steps. This becomes the
  skeleton of the black-box tests, so vagueness here becomes untestable work.
- **Capabilities delivered.** Each with a verify command decided now.
- **Showcase.** How it gets demonstrated. If the answer is "the tests pass",
  there is no showcase yet — keep going.

Exit this loop when every capability has a verify command you could run today
if the code existed. If you cannot name one, that capability is either not
well defined or does not belong in this slice. Both are findings — act on them
rather than writing `TODO`.

## Loop B — explode each subsystem

For each subsystem the slice touches:

    python3 .sprout/sprout.py new exploded-spec <subsystem>

Describe **intent and interface**, scoped to what this slice needs — not a
complete future design. If a subsystem already has a spec, revise it in place
and bump `version`; never create a parallel document.

The discipline: anything a unit or end-to-end test could pin down belongs in a
test, not here. Specs say what callers may rely on; tests say exactly what
happens. Ask "could I write a test that proves this?" If yes, write the test
instead.

Do not omit **failure modes**. Callers depend on failure behaviour as much as
success behaviour, so it is part of the interface. For each condition, state
what the caller observes.

Exit this loop when every touched subsystem has a current spec whose interface
covers every walkthrough step, failure modes included.

## Then record intent

Add the capabilities to `INVENTORY.md` as `planned`, each pinned to the current
version of its spec, and run `python3 .sprout/sprout.py check`.

## Exit — success

- Slice doc has value, walkthrough, capabilities and a real showcase
- Every capability has a decided verify command
- Every touched subsystem has a current exploded spec with failure modes
- Inventory rows exist as `planned`, correctly pinned
- `sprout check` passes

Then: `sprout-build`.

## Exit — failure

- **Too big.** Walkthrough beyond ~7 steps, or more than 3 subsystems touched.
  Split it and spec the first part only. Do not proceed hoping it shrinks.
- **Not showable.** If no showcase can be described, this is a task, not a
  slice. Either fold it into a slice that is showable, or get explicit
  agreement from the user that you are building something unshowable and why.
- **Needs an unnamed subsystem.** The slice requires a subsystem the overview
  spec does not name. Stop; go to `sprout-spec` and update the overview first.
- **A capability resists verification.** After two passes you still cannot name
  a verify command. Say so explicitly. Usually the capability is really a
  quality ("it feels fast") that needs restating as something measurable, or it
  needs a spike to discover how to observe it.
- **An unknown blocks the interface.** You cannot state a subsystem's interface
  without knowing something you do not know. Run `sprout-spike` on it.
