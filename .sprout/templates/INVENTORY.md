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

Run `sprout check` to validate this file, `sprout verify` to execute it.

| ID | Capability | Status | Spec | Ver | Verify |
|---|---|---|---|---|---|
