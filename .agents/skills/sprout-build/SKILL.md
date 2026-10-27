---
name: sprout-build
description: Implement a slice using a strict test-first loop - write black-box end-to-end tests, confirm they fail for the anticipated reason, then write the implementation. Use when starting or continuing implementation of a specced slice, or whenever the user asks to build, implement or code something that has a slice doc.
---

# Build

Two nested loops. Loop A drives the tests to a *predicted* failure; Loop B
drives them to green. The order is not negotiable: the value of a passing test
is that you watched it fail first, for a reason you called in advance.

## Invariant

Tests are never weakened to accommodate the implementation.

If a test is genuinely wrong, fixing it is a deliberate, stated act — announce
what was wrong, why, and what you changed. It is never a quiet convenience on
the way to green. An agent that edits tests to pass has destroyed the only
evidence the method produces.

## Enter when

All of these hold. If any fails, route instead of starting:

| Missing | Go to |
|---|---|
| Slice doc with a walkthrough | `sprout-slice` |
| Current exploded spec per touched subsystem | `sprout-slice` |
| Inventory rows for the capabilities | `sprout-slice` |
| `sprout check` clean | fix the drift first |

Then mark the rows you are working on as `building`.

## Loop A — reach predicted failure

Write every black-box test for the slice before implementing anything. Resist
writing one test and implementing it; you lose the shape of the whole.

**Black-box means black-box.** Tests exercise the system the way a user or
calling client does: real entry point, real behaviour. No importing internals,
no reaching into private state, no asserting on log lines, no mocking the thing
under test. If a test would need to change when a *correct* refactor happens,
it is testing the wrong surface.

Assert what the exploded spec says callers may rely on, failure modes included.
A slice whose tests cover only the happy path is half tested.

Then, each pass: **write down how you expect each test to fail**, run them, and
compare.

    <test command>

| Observed | Meaning | Action |
|---|---|---|
| Fails as predicted | Wired to real behaviour | Exit to Loop B |
| Passes | Not testing what you think, or already built | Fix the test. Never proceed on green |
| Fails differently | Your model of the system is wrong | Stay in Loop A |

The third row is where this loop earns its keep. An unexpected failure is
information about a wrong assumption, and now is the cheapest moment to learn
it. Usual causes: a missing fixture, a harness that never reached your code, or
an interface that does not exist in the shape the spec implied. Diagnose, fix
your understanding — or the test — and go round again.

Never skip the prediction because the outcome seems obvious. The prediction is
the test of your model, not of the code.

**Exit to Loop B** when every test fails for the reason you predicted.

## Loop B — reach green

Write the smallest implementation that satisfies the tests while honouring the
exploded spec's interface and invariants.

Each pass: implement, run the tests, inspect what moved.

- Do not add capability the slice did not ask for.
- If you find the spec is wrong, note it for the tidy pass and keep going.
  Fixing specs mid-implementation loses the record of what was learned.
- If a previously passing test breaks, stop and understand why before
  continuing. A regression you implement past is one you ship.

**Exit** when all tests pass and none were weakened.

## Then wire up verification

Create the verify command each inventory row promised: a script under `verify/`
or a make target, a single invocation, exits non-zero on failure, runnable by
hand.

Flip the rows to `built` and prove it:

    python3 .sprout/sprout.py check
    python3 .sprout/sprout.py verify

A row is `built` only when its verify command passes — not when the code looks
finished, and not when the tests happen to pass some other way.

## Exit — success

- Every walkthrough step has a black-box test
- Each test was observed failing for its predicted reason before implementation
- Tests pass without having been weakened
- Verify commands exist, are single invocations, and pass
- `sprout check` and `sprout verify` are both clean

Then: `sprout-tidy`.

## Exit — failure

Each of these is a real outcome. Report it and route; do not grind.

- **Loop A will not converge.** Three passes and the failure still surprises
  you. Your model of the system is wrong at a level the spec does not capture.
  Stop and run `sprout-spike` on the mechanism you are misreading.
- **Green is unreachable without weakening a test.** The spec and the reality
  disagree. Stop. Say which, and why. Go to `sprout-spec` or `sprout-slice` to
  fix the spec, then re-enter. Never resolve this by editing the test.
- **Green needs violating a spec'd invariant.** Same handling: the spec is
  wrong or the slice is wrong, and both are decisions above this skill.
- **The slice is bigger than specced.** Implementation reveals work the slice
  did not account for. Do not silently expand. Finish what is in scope, report
  what is missing, and let the user decide whether to re-slice.
- **A capability cannot be verified after all.** The promised verify command
  turns out to be impossible. The capability does not exist until it can be
  checked — leave the row as `building`, never mark it `built`, and raise it.
