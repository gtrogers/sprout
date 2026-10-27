---
name: sprout-tidy
description: Fold what implementation taught back into the specs, bump versions and reconcile the inventory. Use after a slice's tests pass and before showcasing it, or whenever specs have fallen out of step with what the code actually does.
---

# Tidy

Implementation always teaches you something the specs got wrong. This closes
that gap while the knowledge is still fresh. Skip it and the specs quietly
become fiction — and once a reader has caught a spec lying, they stop trusting
all of them.

**Tidy is for what implementation taught you — not for work you deferred.**
Updating a template, a skill or a document that your own spec change made
wrong is part of the build loop. If you can see the consequence at spec time,
it is not a learning.

## Invariant

A spec that no longer matches reality is a bug, and is fixed at its own
altitude. Reality discovered in code belongs in the spec as *intent*, not as a
transcription of the implementation.

The pull during tidy is to paste what you built into the spec. That produces an
accurate document at the wrong altitude, which is worse than a stale one: it
freezes an implementation and removes the freedom the spec existed to protect.

## Enter when

- A slice's tests pass and `sprout verify` is clean, or
- Specs are known to have drifted from the code.

Start by gathering the learnings you parked during `sprout-build`, plus a
re-read of each exploded spec the slice touched against what you actually
built.

## Loop

One learning per pass. For each:

1. **Classify it.** Which is it?
   - Spec was wrong about intent → fix the spec, bump `version`
   - Spec was wrong about an interface → fix the interface, bump `version`
   - Spec was silent on a failure mode you hit → add it, bump `version`
   - Spec was right; the code diverged → fix the code, not the spec
   - A detail a test already pins down → belongs nowhere in the spec. Delete it
     if it crept in
   - Overview-level: a subsystem boundary or constraint is wrong → route to
     `sprout-spec`, do not quietly reshape the overview here
2. **Apply the smallest edit** at the right altitude.
3. **Bump `version`** if you changed a spec's substance. Typo fixes do not count.
4. **Close the gap you just opened.** Bumping a spec puts that subsystem behind
   again, which `sprout next` will report. Re-run its verify command, and raise
   `implemented` to the new version only if it passes. If it fails, leave
   `implemented` where it is: the subsystem genuinely no longer meets its spec.
5. **Run the checks.**

       python3 .sprout/sprout.py check
       python3 .sprout/sprout.py verify

Repeat until no learnings remain and both commands are clean.

Then sweep for ledger rot, which accumulates silently:

- Rows for subsystems that no longer exist — delete them, and their specs
- Exploded specs with no row — `check` catches these, but understand why it
  happened before adding one
- Subsystems left behind their specs from a finished slice — either finish them
  or revert the spec; a permanent gap is a lie about what is planned

## Exit — success

- Every parked learning is classified and applied
- Changed specs have bumped versions
- Every subsystem's `implemented` was raised only after re-verifying
- `sprout check` and `sprout verify` are both clean
- No spec contains detail a test already pins down

Then: `sprout-showcase`.

## Exit — failure

- **A learning invalidates the overview spec.** Subsystem boundaries or
  constraints turned out wrong. Too big for tidy — go to `sprout-spec`, then
  return.
- **A re-verified subsystem now fails.** Something implemented has regressed,
  or was never really verified. Leave `implemented` where it is and report it.
  Never raise it to make a gap disappear.
- **A learning keeps reopening settled specs.** Two passes touching the same
  spec in contradictory directions means the design is unresolved, not untidy.
  Stop and raise it with the user.
