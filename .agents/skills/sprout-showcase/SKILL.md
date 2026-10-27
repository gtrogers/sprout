---
name: sprout-showcase
description: Demonstrate a finished slice by bringing the app up in a state where the work can be tried, or producing other usable proof, then run tight feedback loops on what comes back. Use when a slice is built and tidied, or when the user asks to show, demo or try out what was just built.
---

# Showcase

A slice is not done when the tests pass. It is done when the user has seen it
and had the chance to react. Tests prove the thing works; a showcase proves it
is the right thing.

## Invariant

The user must be able to exercise the work themselves. Your report of what
happened is not a showcase — it removes exactly the judgement the showcase
exists to collect.

## Enter when

- A slice is built and tidied, `sprout check` and `sprout verify` are clean.
- The slice doc names a showcase. If it does not, write one now.

## Loop A — produce the proof

Each pass, get closer to something the user can drive. In descending order of
preference:

1. **The app running, in the right state.** Launched, seeded, sitting on the
   screen where the new capability is reachable. Give the exact command, the
   URL or entry point, and the credentials or fixtures needed. Say what to look
   for and what they should expect to see.
2. **A driveable artifact.** A CLI they invoke, a script producing visible
   output, a rendered page. Still theirs to run.
3. **Captured proof**, only when the first two are impossible — a screenshot, a
   recording, a transcript. State plainly why you fell back, since this is the
   weakest form and the user should know they are getting it.

Verify the showcase works before presenting it. A broken demo spends the user's
attention on your mistake instead of on the work.

Exit when there is something the user can actually try, with instructions short
enough to follow without asking a follow-up question.

## Loop B — act on feedback

Feedback is the point. Expect it, and expect most of it to be about things
specs do not capture well: wording, pacing, layout, friction, surprise.

Each pass:

1. **Classify what came back.**
   - Cosmetic or small UX, inside the slice's intent → fix it here, in this
     loop. Re-show immediately. Keep these turns small and fast.
   - A real behaviour bug → go to `sprout-build`: write the black-box test that
     should have caught it, watch it fail, then fix. Never patch a behaviour
     bug directly from a showcase; that is how untested fixes enter.
   - Intent was wrong → the spec is wrong. Route to `sprout-spec` or
     `sprout-slice`. Do not absorb a change of intent as a tweak.
   - New capability → a new slice. Say so rather than growing this one.
2. **Apply, re-show, and ask again.** Short loops: one or two changes per
   round, not a batch.

Keep cycling until the user is satisfied or defers the rest.

If a fix touched anything beyond cosmetics, run `sprout check` and
`sprout verify` again before closing. Small UX fixes break verify commands more
often than you would expect.

## Exit — success

- The user has exercised the work themselves
- Feedback is resolved, or explicitly deferred with a note of what was deferred
- Behaviour bugs found here got tests, not just fixes
- `sprout check` and `sprout verify` clean after any changes
- The ledger reflects what is actually there: no subsystem claims a version it
  does not meet

Then: `sprout-slice` for the next slice.

## Exit — failure

- **It cannot be brought up.** The slice does not integrate into a runnable
  whole. That is a finding about the slice, not a presentation problem — report
  it and expect to re-slice.
- **Feedback keeps reopening intent.** Two rounds where each answer changes what
  the thing is for means the spec never captured the intent. Stop fixing and go
  to `sprout-spec`.
- **Fixes break verification.** If small changes keep breaking verify commands,
  the commands are testing implementation rather than capability. Raise it in
  `sprout-tidy` rather than loosening them.
