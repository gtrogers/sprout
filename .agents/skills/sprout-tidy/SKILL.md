---
name: sprout-tidy
description: Fold what implementation taught back into the specs, bump versions and reconcile the inventory. Use after a slice's tests pass and before showcasing it, or whenever specs have fallen out of step with what the code actually does.
---

# Tidy

Implementation always teaches you something the specs got wrong. This closes
that gap while the knowledge is still fresh. Skip it and the specs quietly
become fiction — and once a reader has caught a spec lying, they stop trusting
all of them.

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
4. **Re-pin the inventory.** Bumping drifts every row pinned to that spec, so
   `sprout check` will fail. For each drifted row: re-run its verify command,
   and re-pin only if it passes. A row whose verify now fails goes back to
   `building` — it is no longer built.
5. **Run the checks.**

       python3 .sprout/sprout.py check
       python3 .sprout/sprout.py verify

Repeat until no learnings remain and both commands are clean.

Then sweep for inventory rot, which accumulates silently:

- Rows marked `built` whose capability was dropped — delete them
- Capabilities that exist in code but have no row — add them, or delete the code
- Rows still `building` from a finished slice — resolve each either way

## Exit — success

- Every parked learning is classified and applied
- Changed specs have bumped versions
- No drifted rows; every re-pinned row was re-verified, not just re-pinned
- `sprout check` and `sprout verify` are both clean
- No spec contains detail a test already pins down

Then: `sprout-showcase`.

## Exit — failure

- **A learning invalidates the overview spec.** Subsystem boundaries or
  constraints turned out wrong. Too big for tidy — go to `sprout-spec`, then
  return.
- **A re-verified row now fails.** Something that was built has regressed, or
  was never really verified. Set it back to `building` and report it. Do not
  re-pin a failing row to make the check pass.
- **A learning keeps reopening settled specs.** Two passes touching the same
  spec in contradictory directions means the design is unresolved, not untidy.
  Stop and raise it with the user.
