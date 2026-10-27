---
id: document-kinds
kind: exploded-spec
version: 2
status: active
parent: overview
---

# Document kinds

## Purpose

Define the four document types, the altitude each occupies, and how new ones are
created from templates.

## Responsibilities

- Define `spec`, `exploded-spec`, `slice` and `spike` as the complete set
- Own the frontmatter contract every document obeys
- Scaffold new documents from templates with identity fields filled in

## Explicitly not responsible for

- Judging a document's content or altitude — that is the author's job, guided by
  the skills
- Rendering, publishing or cross-linking documents

## Interface

### Frontmatter contract

Every document opens with flat `key: value` frontmatter between `---` fences.
Nesting is not supported, which is a deliberate bound rather than a limitation
to work around.

| Field | Meaning |
|---|---|
| `id` | Lowercase-hyphenated, must equal the filename stem |
| `kind` | One of the four kinds |
| `version` | Monotonic positive integer, bumped on substantive change |
| `status` | Valid values depend on `kind` — see Lifecycles |
| `parent` | Optional; for exploded specs, the spec they derive from |

### Lifecycles

`status` is kind-specific. Documents that describe intent move through an
editorial lifecycle; a slice moves through a delivery lifecycle, because a
slice is a unit of work rather than a description of one.

| Kind | Valid statuses |
|---|---|
| `spec`, `exploded-spec`, `spike` | `draft`, `active`, `superseded` |
| `slice` | `planned`, `building`, `built`, `showcased` |

A slice is `built` when every capability it delivers is `built`, and
`showcased` only after it has been demonstrated and the resulting feedback
resolved. The distinction exists so that a delivered-but-unshown slice is a
visible, addressable state — showcase is the loop most easily skipped, and an
unrepresentable state is a skippable one.

### Altitudes

| Kind | Altitude | Lives in |
|---|---|---|
| `spec` | Project goals and intent; subsystems named, not designed | `specs/` |
| `exploded-spec` | One subsystem's intent and interface, scoped to a slice | `exploded-specs/` |
| `slice` | One deliverable end-to-end piece of work | `slices/` |
| `spike` | One timeboxed question, distilled to a page | `spikes/` |

The shared rule across all four: anything a test could pin down belongs in a
test, not in a document.

### Scaffolding

`new <kind> <name>` creates `<dir>/<name>.md` from the matching template,
substituting `{{id}}`, `{{title}}` and `{{date}}`.

### Failure modes

| Condition | Observable result |
|---|---|
| Name is not lowercase-hyphenated | Exits 2, explains the naming rule |
| Target file already exists | Exits 2, refuses; never overwrites |
| Template missing | Exits 2, names the expected template path |

## Invariants

- A scaffolded document passes `check` immediately, with no placeholders left in
  its frontmatter.
- `id` always equals the filename stem, so a document can be found from a
  reference and vice versa.

## Depends on

- Templates in `.sprout/templates/`, one per kind.
