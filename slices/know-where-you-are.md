---
id: know-where-you-are
kind: slice
version: 1
---

# Know where you are

> **Partly superseded by `slice-state-is-derived`.** This slice introduced a
> declared slice lifecycle including a `showcased` state. That state was later
> removed: it was an unverifiable self-report, which is exactly what the method
> refuses elsewhere. Slice state is now derived from the inventory rows naming
> the slice, and the capability `slice-lifecycle-is-representable` was retired.
> The walkthrough below is kept as the record of what was delivered at the
> time; steps 4 and 6 describe behaviour that no longer exists.

## Value

Returning to a project — or starting a fresh agent session on one — you can run
one command and be told which loop you are in, what is blocking the next
transition, and what to do about it. Nobody has to reconstruct state that lived
in a context window that is gone.

## Walkthrough

1. In a project mid-slice, run `sprout next`. It names the loop, the reason,
   the blocker and the next action.
2. Bump a spec's version. Run `sprout next`; it now routes to `sprout-tidy`,
   because drift outranks progress.
3. Re-pin, then run `sprout next`; it routes back to the loop that was in flight.
4. Mark a slice's capabilities `built` but leave the slice unshowcased. Run
   `sprout next`; it routes to `sprout-showcase` rather than to the next slice.
5. Run `sprout next` in a freshly installed, empty project; it routes to
   `sprout-spec` rather than erroring.
6. Set a slice's status to a value outside its lifecycle. Run `sprout check`;
   it fails and names the valid statuses for that kind.
7. Run `sprout next --json` and get the same position as a machine-readable
   object.

## Subsystems touched

| Subsystem | Exploded spec | New or changed |
|---|---|---|
| Navigator | `exploded-specs/navigator.md` | New |
| Document kinds | `exploded-specs/document-kinds.md` | Changed — slice lifecycle, kind-specific statuses |
| Checker | `exploded-specs/checker.md` | Changed — validate status against kind |

## Capabilities delivered

| ID | Capability | Verify |
|---|---|---|
| `slice-lifecycle-is-representable` | A slice's delivery state, including built-but-unshowcased, is representable and validated | `python3 verify/verify.py slice-lifecycle-is-representable` |
| `check-validates-status-per-kind` | Documents cannot carry a status outside their kind's lifecycle | `python3 verify/verify.py check-validates-status-per-kind` |
| `next-reports-position` | One command names the current loop, its reason, the blocker and the next action | `python3 verify/verify.py next-reports-position` |
| `next-precedence-is-deterministic` | The same artifacts always resolve to the same position, by published precedence | `python3 verify/verify.py next-precedence-is-deterministic` |
| `next-survives-degenerate-projects` | Empty, uninitialised and unparseable projects all yield a position or a clear refusal | `python3 verify/verify.py next-survives-degenerate-projects` |

## Out of scope

- **The observation log.** `next` derives position from artifacts only. Build
  sub-loop position (Loop A versus Loop B) is therefore not reported, and
  `next` says so rather than guessing. The log is the following slice.
- Spikes blocking dependent loops; needs a spike-to-decision link that may cost
  more bookkeeping than it earns.
- Any migration of existing slice statuses beyond this repository's own.
- `next` suggesting *which* slice to do next. It reports position, not strategy.

## Showcase

    python3 .sprout/sprout.py next              # mid-slice, in this repo
    python3 .sprout/sprout.py next --json

Then walk the precedence ladder live, which is the part worth watching:

    sed -i '' 's/^version: 2$/version: 3/' exploded-specs/checker.md
    python3 .sprout/sprout.py next              # -> tidy, drift outranks progress
    sed -i '' 's/^version: 3$/version: 2/' exploded-specs/checker.md
    python3 .sprout/sprout.py next              # -> back to the slice in flight

And in a fresh project, to show the empty case routes rather than errors:

    python3 install.py /tmp/demo2
    cd /tmp/demo2 && python3 .sprout/sprout.py next   # -> sprout-spec

## Done when

- [ ] Black-box tests written, and observed failing in the code under test
- [ ] Implementation complete, tests passing
- [ ] `sprout check` and `sprout verify` both clean
- [ ] Inventory rows added, pinned to current spec versions
- [ ] Specs reconciled with what was actually learned
- [ ] Showcase produced
