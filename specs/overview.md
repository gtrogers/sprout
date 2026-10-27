---
id: overview
kind: spec
version: 1
status: active
---

# Sprout

> Sprout is specced with its own method. This document is the overview spec,
> and the thing it describes is the framework you are reading.

## Problem

Spec-driven development with coding agents tends to fail in one of two
directions. Lightweight approaches are just prose, so nothing stops an agent
declaring success it has not earned. Heavyweight approaches add personas,
pipelines and ceremony that cost more attention than the code they produce, and
they bind you to one agent.

What is missing in both is an *arbiter*: something outside the agent's narrative
that decides whether work exists. Agents are fluent, and fluency about one's own
output is indistinguishable from completion unless something external checks.

## Goals

- A developer can carry one method across every coding agent they use, because
  the method lives in files the agents already read.
- An agent cannot credibly claim work is done when it is not; a single command
  settles it.
- Specs stay trustworthy over a project's life, because drift between spec and
  reality is detected mechanically rather than noticed eventually.
- An agent that gets stuck recognises it and says so, instead of thrashing or
  quietly lowering the bar.
- The whole framework can be read and understood in one sitting.

## Non-goals

- **Not a build tool, test runner or task manager.** Sprout invokes the
  project's own commands; it never replaces them.
- **Not agent orchestration.** No personas, no multi-agent handoffs, no
  delegation graph. One agent, one loop at a time.
- **Not project management.** The inventory records what exists and how it is
  checked. Not estimates, assignees, dates or velocity.
- **Not a judge of code quality.** Sprout checks that capabilities are verified,
  never whether the implementation is good.
- **No prescribed language, stack or test framework.** Sprout cares that a
  verify command exists and exits zero.
- **Not a hosted service.** No account, no network, no telemetry.

## Subsystems

| Subsystem | Purpose |
|---|---|
| Document kinds | The four document types and what altitude each occupies |
| Inventory | The ledger that decides what exists, and the verification contract |
| Checker | Deterministic validation of specs, inventory and drift |
| Verifier | Executes the inventory's verify commands and reports honestly |
| Skills | The loops an agent follows, with explicit success and failure exits |
| Distribution | Getting sprout into a project and wiring every agent's entry point |

## Constraints

- **Stdlib only, Python 3.9+.** A dependency to install is a reason not to adopt
  it, and agents cannot reliably install things.
- **Cross-platform in one implementation.** No parallel shell and PowerShell
  scripts to drift apart.
- **Skills use only `name` and `description` frontmatter.** Everything else in
  the Agent Skills standard is read by some agents and ignored by others.
- **Inventory is human-readable.** It is read and edited by hand far more often
  than by machine, so a markdown table, not a data file.
- **No YAML parser available**, which bounds frontmatter to flat key–value
  pairs. Acceptable: nesting would be at the wrong altitude anyway.
- **Agents discover skills at different paths**, so one canonical location with
  links is the only arrangement that works everywhere.

## Invariants

- A capability is `built` only if a verify command exists and exits zero. There
  is no second route to `built`.
- Every spec carries a monotonic integer `version`.
- Every inventory row pins the spec version it was built against; a mismatch is
  a check failure, not a warning.
- Verify commands are single invocations, so a human can run any one of them by
  hand without knowing a shell.
- `sprout check` and `sprout verify` are pure: they report, and change nothing.
- Every skill names its failure exits and where to go instead, so being stuck
  is a state an agent can detect rather than a loop it cannot leave.
- Sprout's own capabilities are verified by sprout.

## Open questions

- Should drift distinguish editorial from substantive spec changes? Currently
  any version bump drifts every pinned row, which is safe but noisy on large
  projects. Monotonic integers were chosen over semver to keep bumping
  unambiguous; the cost is that noise.
- Should `verify` support parallel execution? Irrelevant until a real project
  has enough rows for it to hurt.
- Is a fifth document kind needed for cross-cutting decisions (an ADR), or does
  a spike plus a spec bump cover it?
