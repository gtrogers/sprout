# Sprout

Sprout is a cross-agent framework for spec-driven, slice-based delivery. This
repository is both the framework and a worked example of it: sprout is specced,
sliced and verified with its own method.

If you are an agent working in this repo, you are working on the method itself.
Read `specs/overview.md` first, then `slices/self-hosting-core.md`.

Changes to the method must survive its own checks:

    python3 verify/verify.py --all
    python3 .sprout/sprout.py check
    python3 .sprout/sprout.py verify

## How work happens here (sprout)

This project is built in **slices**: valuable, end-to-end, deliverable pieces
of work. Specs describe intent and interface; tests pin down behaviour.

Non-negotiables:

1. **Unverifiable means not implemented.** A subsystem counts as implemented at
   a version only when `INVENTORY.csv` carries a verify command that passes. No
   deterministic, programmatic check means it is not done, however complete the
   code looks.
2. **Tests before implementation.** Write black-box, end-to-end tests first,
   run them, and confirm they fail for the anticipated reason. A test that
   passes before implementation, or fails for the wrong reason, is a broken
   test. Only then implement.
3. **Specs are versioned and are not implementation.** Every spec carries
   `version` in YAML frontmatter. Specs state goals, intent, interfaces and
   invariants. If a test could pin it down, it belongs in a test.
   The flow is one-way and specs move first:
   overview spec -> exploded specs -> tests -> implementation -> tidy.
   Changing a goal, constraint or invariant means updating the overview spec
   **before** touching anything else, not at the tidy pass.
4. **The ledger tracks spec versus implementation.** `INVENTORY.csv` records,
   per subsystem, which spec version the code satisfies. A spec ahead of its
   implementation is **work owed**, not an error — it is the queue, and
   `sprout next` reports it. Raise `implemented` only after re-verifying.
5. **Learnings flow back.** When implementation teaches you something the spec
   got wrong, fix the spec and bump its version. Do not leave the spec lying.

**Starting or resuming work?** Do not infer the state of the project. Ask:

    python3 .sprout/sprout.py next

It reports which loop you are in, what is blocking the transition out of it,
and what to do — derived from the artifacts, by fixed precedence. Use it
instead of guessing, and prefer it to re-reading the whole project.

Before claiming any work is complete, both of these must be clean:

    python3 .sprout/sprout.py check
    python3 .sprout/sprout.py verify

Available skills: `sprout-spec`, `sprout-slice`, `sprout-build`,
`sprout-tidy`, `sprout-showcase`, `sprout-spike`.
