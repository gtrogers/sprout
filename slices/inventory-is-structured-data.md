---
id: inventory-is-structured-data
kind: slice
version: 1
---

# Inventory is structured data

## Value

The ledger is stored as structured data rather than a presentation format, so
it survives punctuation, diffs and merges cleanly — and every capability names
the slice that delivers it, which is what lets slice state be computed instead
of declared.

## Walkthrough

1. Open `INVENTORY.csv`; it is a CSV with a header row, one row per capability.
2. Add a capability whose description contains a comma and an apostrophe. Run
   `sprout check`; it parses correctly, with no escaping by hand.
3. Point a row at a slice that does not exist. `sprout check` fails and names
   the missing slice.
4. Remove a required column. `sprout check` fails, naming the column, and does
   not misparse the remaining rows.
5. Run `sprout status` and `sprout verify`; both read the new format and report
   exactly as before.
6. Install into a fresh project; it is created with `INVENTORY.csv`, header
   only, and passes `sprout check`.

## Subsystems touched

| Subsystem | Exploded spec | New or changed |
|---|---|---|
| Inventory | `exploded-specs/inventory.md` | Changed — CSV storage, slice column |
| Checker | `exploded-specs/checker.md` | Changed — CSV parsing, slice reference validation |
| Distribution | `exploded-specs/distribution.md` | Changed — ships `INVENTORY.csv` |

## Capabilities delivered

| ID | Capability | Verify |
|---|---|---|
| `inventory-is-csv` | The ledger is CSV, so punctuation in any field survives without hand-escaping | `python3 verify/verify.py inventory-is-csv` |
| `inventory-rows-name-their-slice` | Every capability names the slice delivering it, and dangling references are caught | `python3 verify/verify.py inventory-rows-name-their-slice` |
| `check-rejects-malformed-inventory` | Missing columns and malformed rows are reported with their line numbers | `python3 verify/verify.py check-rejects-malformed-inventory` |

## Out of scope

- Deriving slice state from rows. The column lands here; the computation is the
  next slice.
- A shipped migration command. Sprout is the only project on the old format, so
  it is migrated once by hand rather than carrying a tool for it forever.
- Typed fields. `ver` stays a string and is parsed, which is what CSV costs and
  it is not worth JSON's merge behaviour to avoid.

## Showcase

    python3 .sprout/sprout.py check
    python3 .sprout/sprout.py status
    head -3 INVENTORY.csv

Then show the format earning itself — a description that would have broken a
markdown table:

    python3 .sprout/sprout.py check     # after adding a row containing , and '

And a fresh install:

    python3 install.py /tmp/demo4 && cd /tmp/demo4 && python3 .sprout/sprout.py check

## Done when

- [ ] Black-box tests written, and observed failing in the code under test
- [ ] Implementation complete, tests passing
- [ ] `sprout check` and `sprout verify` both clean
- [ ] Inventory rows added, pinned to current spec versions
- [ ] Specs reconciled with what was actually learned
- [ ] Showcase produced
