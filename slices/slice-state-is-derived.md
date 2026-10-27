---
id: slice-state-is-derived
kind: slice
version: 1
---

# Slice state is derived

> This slice's own frontmatter carries no `status`, which is the change it
> makes. Until it is built the Checker still demands one, so this document is
> invalid by the current rules — deliberately. The first test written proves
> exactly that.

## Value

A slice can no longer claim to be further along than the capabilities it
delivers. Its state is computed from the ledger rather than declared by whoever
last edited the file, so nothing about progress is self-reported.

## Walkthrough

1. Open any slice document; it has no `status` field.
2. Add one. Run `sprout check`; it fails, saying slice state is derived.
3. Set every row of a slice to `built`. Ask `sprout next`; that slice is no
   longer in flight and it routes onward.
4. Set one row back to `building`. `sprout next` reports that slice building
   again, with no file edited but the ledger.
5. Confirm no `showcased` state exists anywhere, and that `next` prompts for
   showcasing in its action text instead.

## Subsystems touched

| Subsystem | Exploded spec | New or changed |
|---|---|---|
| Document kinds | `exploded-specs/document-kinds.md` | Changed — slices declare no status |
| Navigator | `exploded-specs/navigator.md` | Changed — precedence reads derived state |

## Capabilities delivered

| ID | Capability | Verify |
|---|---|---|
| `slice-state-is-derived-from-rows` | A slice's state is computed from the rows naming it, never declared | `python3 verify/verify.py slice-state-is-derived-from-rows` |
| `check-rejects-declared-slice-status` | A slice that declares a status is rejected, so the self-report cannot return | `python3 verify/verify.py check-rejects-declared-slice-status` |
| `next-routes-on-derived-slice-state` | Routing follows the ledger, so changing a row changes the reported loop | `python3 verify/verify.py next-routes-on-derived-slice-state` |

## Out of scope

- Routing to showcase on evidence. That needs recorded showcase events, which
  is the observation log slice.
- Deriving editorial status for specs and spikes. Those genuinely are editorial
  judgements with nothing to compute them from.

## Showcase

    python3 .sprout/sprout.py next
    grep -c '^status:' slices/*.md          # zero
    # flip a row in INVENTORY.csv and watch next follow it

## Done when

- [ ] Black-box tests written, and observed failing in the code under test
- [ ] Implementation complete, tests passing
- [ ] `sprout check` and `sprout verify` both clean
- [ ] Inventory rows added, pinned to current spec versions
- [ ] Specs reconciled with what was actually learned
- [ ] Showcase produced
