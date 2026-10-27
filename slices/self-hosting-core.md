---
id: self-hosting-core
kind: slice
version: 1
status: showcased
---

# Self-hosting core

## Value

A developer can install sprout into any project, follow the method with
whichever agent they use, and run one command that settles whether the work
they were promised actually exists.

## Walkthrough

1. Run `python3 install.py <project>`; the tooling, skills and every agent's
   entry point are wired up in one step.
2. Open the project in any conforming agent; it discovers the six sprout skills
   and reads the invariants from `AGENTS.md`.
3. Scaffold an overview spec with `sprout new spec overview` and write it.
4. Scaffold a slice, explode the subsystems it touches, and record the
   capabilities as `planned` with their verify commands decided.
5. Build the slice test-first, then wire up each promised verify command.
6. Run `sprout check`; specs are versioned, the inventory is consistent, no row
   is pinned to a stale spec.
7. Run `sprout verify`; every `built` capability's command executes and passes.
8. Bump a spec's version and run `sprout check` again; every row pinned to it
   now fails as drift, and keeps failing until each is re-verified and re-pinned.

## Subsystems touched

| Subsystem | Exploded spec | New or changed |
|---|---|---|
| Document kinds | `exploded-specs/document-kinds.md` | New |
| Inventory | `exploded-specs/inventory.md` | New |
| Checker | `exploded-specs/checker.md` | New |
| Verifier | `exploded-specs/verifier.md` | New |
| Skills | `exploded-specs/skills.md` | New |
| Distribution | `exploded-specs/distribution.md` | New |

## Capabilities delivered

See `INVENTORY.md` for the authoritative rows. Ten capabilities, each verified
by a black-box test that drives the CLI as a subprocess in a throwaway project.

## Out of scope

- Parallel execution of verify commands
- Distinguishing editorial from substantive spec changes when drifting rows
- An ADR document kind for cross-cutting decisions
- Any form of packaging beyond `install.py`

## Showcase

    python3 install.py /tmp/demo        # wire up a fresh project
    cd /tmp/demo && python3 .sprout/sprout.py check
    python3 .sprout/sprout.py new spec overview

Then, in this repo, the arbiter turned on itself:

    python3 verify/verify.py --all
    python3 .sprout/sprout.py status

To watch drift detection work, bump `version` in any exploded spec and re-run
`python3 .sprout/sprout.py check`.

## Done when

- [x] Black-box tests written, and observed failing for the anticipated reason
- [x] Implementation complete, tests passing
- [x] `sprout check` and `sprout verify` both clean
- [x] Inventory rows added, pinned to current spec versions
- [x] Specs reconciled with what was actually learned
- [x] Showcase produced
