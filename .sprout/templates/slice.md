---
id: {{id}}
kind: slice
version: 1
status: planned
---

# {{title}}

> A valuable, end-to-end, deliverable piece of work. If it cannot be shown to
> someone and understood without explanation, it is not a slice — it is a task.

## Value

What a user can do after this slice that they could not do before. One
sentence, in their language, not the system's.

## Walkthrough

The end-to-end path this slice makes work, as a sequence of observable steps.
This is the skeleton the black-box tests will follow.

1. 
2. 
3. 

## Subsystems touched

Each needs a current exploded spec before implementation starts.

| Subsystem | Exploded spec | New or changed |
|---|---|---|
|  |  |  |

## Capabilities delivered

Rows to add to `INVENTORY.md`. Every one needs a verify command that will exist
by the end of the slice — decide it now, while it is still cheap to shape the
work around being verifiable.

| ID | Capability | Verify |
|---|---|---|
|  |  |  |

## Out of scope

What stays unbuilt, so the slice can actually land.

- 

## Showcase

How this gets demonstrated when it is done. "Run `X`, then do `Y`, and you will
see `Z`." If the answer is "the tests pass", the slice has no showcase yet.

## Done when

- [ ] Black-box tests written, and observed failing for the anticipated reason
- [ ] Implementation complete, tests passing
- [ ] `sprout check` and `sprout verify` both clean
- [ ] Inventory rows added, pinned to current spec versions
- [ ] Specs reconciled with what was actually learned
- [ ] Showcase produced
