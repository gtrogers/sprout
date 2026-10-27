<!-- Paste into your AGENTS.md / CLAUDE.md. These are the always-on invariants;
     the method itself lives in the sprout skills and loads on demand. -->

## How work happens here (sprout)

This project is built in **slices**: valuable, end-to-end, deliverable pieces
of work. Specs describe intent and interface; tests pin down behaviour.

Non-negotiables:

1. **Unverifiable means nonexistent.** A capability counts as built only when
   `INVENTORY.md` lists it with a verify command that passes. No deterministic,
   programmatic check means it does not exist, however complete the code looks.
2. **Tests before implementation.** Write black-box, end-to-end tests first,
   run them, and confirm they fail for the anticipated reason. A test that
   passes before implementation, or fails for the wrong reason, is a broken
   test. Only then implement.
3. **Specs are versioned and are not implementation.** Every spec carries
   `version` in YAML frontmatter. Specs state goals, intent, interfaces and
   invariants. If a test could pin it down, it belongs in a test.
4. **The inventory pins spec versions.** Revising a spec drifts every row
   pinned to it, and `sprout check` fails until each is re-verified and
   re-pinned.
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
