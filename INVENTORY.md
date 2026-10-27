# Inventory

The ledger of what exists. This file is the arbiter: if a capability is not
listed here as `built` with a passing verify command, it does not exist —
regardless of what the code appears to do.

- **Status** is one of `planned`, `building`, `built`.
- **Spec** is the path to the spec that defines the capability.
- **Ver** pins the spec version it was built against. When a spec is revised,
  pinned rows drift and `sprout check` fails until each is re-verified and
  re-pinned, or reverted.
- **Verify** is a single command — no pipes or redirects. Wrap anything
  compound in a script or make target, so it is runnable by hand too.

Run `python3 .sprout/sprout.py check` to validate this file,
`python3 .sprout/sprout.py verify` to execute it.

| ID | Capability | Status | Spec | Ver | Verify |
|---|---|---|---|---|---|
| cli-check-requires-versioned-specs | Every spec must carry a version, or the project fails its checks | built | exploded-specs/checker.md | 2 | `python3 verify/verify.py cli-check-requires-versioned-specs` |
| cli-check-detects-spec-drift | Revising a spec drifts every inventory row pinned to it | built | exploded-specs/checker.md | 2 | `python3 verify/verify.py cli-check-detects-spec-drift` |
| cli-check-rejects-unverifiable-capabilities | A capability cannot be marked built without a verify command | built | exploded-specs/checker.md | 2 | `python3 verify/verify.py cli-check-rejects-unverifiable-capabilities` |
| cli-check-rejects-shell-metacharacters | Verify commands must be single invocations a human can run by hand | built | exploded-specs/checker.md | 2 | `python3 verify/verify.py cli-check-rejects-shell-metacharacters` |
| cli-check-rejects-duplicate-and-missing-refs | Duplicate IDs and dangling spec references are caught | built | exploded-specs/checker.md | 2 | `python3 verify/verify.py cli-check-rejects-duplicate-and-missing-refs` |
| cli-verify-executes-commands | Verification runs each built capability's command and reports honestly | built | exploded-specs/verifier.md | 1 | `python3 verify/verify.py cli-verify-executes-commands` |
| cli-new-scaffolds-documents | New specs, slices and spikes scaffold from templates, ready to check | built | exploded-specs/document-kinds.md | 2 | `python3 verify/verify.py cli-new-scaffolds-documents` |
| cli-status-reports-progress | The inventory reports what is built, in progress and planned | built | exploded-specs/inventory.md | 1 | `python3 verify/verify.py cli-status-reports-progress` |
| skills-are-cross-agent-portable | Every skill stays within the portable Agent Skills subset | built | exploded-specs/skills.md | 1 | `python3 verify/verify.py skills-are-cross-agent-portable` |
| install-bootstraps-a-project | One command installs sprout and wires up every agent's entry point | built | exploded-specs/distribution.md | 1 | `python3 verify/verify.py install-bootstraps-a-project` |
| slice-lifecycle-is-representable | A slice's delivery state, including built-but-unshowcased, is representable and validated | built | exploded-specs/document-kinds.md | 2 | `python3 verify/verify.py slice-lifecycle-is-representable` |
| check-validates-status-per-kind | Documents cannot carry a status outside their kind's lifecycle | built | exploded-specs/checker.md | 2 | `python3 verify/verify.py check-validates-status-per-kind` |
| next-reports-position | One command names the current loop, its reason, the blocker and the next action | built | exploded-specs/navigator.md | 2 | `python3 verify/verify.py next-reports-position` |
| next-precedence-is-deterministic | The same artifacts always resolve to the same position, by published precedence | built | exploded-specs/navigator.md | 2 | `python3 verify/verify.py next-precedence-is-deterministic` |
| next-survives-degenerate-projects | Empty, uninitialised and unparseable projects all yield a position or a clear refusal | built | exploded-specs/navigator.md | 2 | `python3 verify/verify.py next-survives-degenerate-projects` |
