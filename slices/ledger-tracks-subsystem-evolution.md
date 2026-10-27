---
id: ledger-tracks-subsystem-evolution
kind: slice
version: 1
---

# Ledger tracks subsystem evolution

## Value

The ledger records what matters as a project is built up: for each subsystem,
what its spec says now, which version the implementation satisfies, and how
that is checked. The gap between the two is the work queue, so a spec evolving
ahead of its code is a normal, visible state rather than a check failure.

## Walkthrough

1. Open `INVENTORY.csv`; one row per subsystem — spec path, implemented
   version, verify command. No capability rows.
2. Run `sprout status`; each subsystem shows its spec version, the version
   implemented, and the resulting state.
3. Bump a subsystem's spec version. `sprout check` still passes — the spec has
   simply moved ahead of the code.
4. Run `sprout next`; it routes to the build loop and names the subsystem that
   is now owed work.
5. Re-verify and raise `implemented` to match. `sprout next` reports the slice
   no longer in flight.
6. Set `implemented` above the spec's version. `sprout check` fails: an
   implementation cannot satisfy a version its spec does not have.

## Out of scope

- Recording showcase events. Still waiting on the observation log.
- A `superseded-by` field for slice documents; convention continues for now.
- Per-capability verify commands. Verification is per subsystem: does this
  subsystem meet its spec at the stated version.
- Any declaration of which subsystems a slice touches. Updating an exploded
  spec is that declaration; stating it twice is bookkeeping that can go stale.

## Showcase

    python3 .sprout/sprout.py status
    python3 .sprout/sprout.py next

Then watch a spec evolve ahead of its implementation and become a queue entry
rather than a failure:

    sed -i '' 's/^version: 4$/version: 5/' exploded-specs/checker.md
    python3 .sprout/sprout.py check     # still passes
    python3 .sprout/sprout.py next      # -> build, naming 'checker'

## Done when

- [ ] Black-box tests written, and observed failing in the code under test
- [ ] Implementation complete, tests passing
- [ ] `sprout check` clean, `sprout verify` passing for every subsystem
- [ ] No gaps remain: every subsystem's `implemented` equals its spec version
- [ ] Specs reconciled with what was actually learned
- [ ] Showcase produced
