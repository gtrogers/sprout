---
id: {{id}}
kind: slice
version: 1
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

## Verification

Every subsystem this slice advances needs a verify command in `INVENTORY.csv`
before implementation starts — decide it now, while the work can still be
shaped around being checkable.

Do not list which subsystems the slice touches. Updating their exploded specs
is that declaration; the resulting spec-to-implementation gap is what `sprout
next` reads.

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
