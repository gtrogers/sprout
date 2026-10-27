---
id: document-kinds
kind: exploded-spec
version: 6
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

A slice document declares a goal, not a plan. It names what will be true when
the slice lands; which subsystems that requires is expressed by updating their
exploded specs, not by listing them twice.


### Frontmatter contract

Every document opens with flat `key: value` frontmatter between `---` fences.
Nesting is not supported, which is a deliberate bound rather than a limitation
to work around.

| Field | Meaning |
|---|---|
| `id` | Lowercase-hyphenated, must equal the filename stem |
| `kind` | One of the four kinds |
| `version` | Monotonic positive integer, bumped on substantive change |
| `status` | Editorial kinds only; slices declare none — see Lifecycles |
| `parent` | Optional; for exploded specs, the spec they derive from |

### Lifecycles

Documents that describe intent carry an editorial `status` of `draft`, `active`
or `superseded`.

**A slice declares no status at all**, and no subsystem list either. Both are
derived: the project is mid-slice while any subsystem's `implemented` lags its
spec version, and the slice is delivered once no gap remains. Declaring a
status is rejected.

A slice is a unit of work, and its progress is a fact about how far the
subsystems have caught up with their specs — so it is computed from the ledger
rather than asserted in frontmatter. A declared status is a self-report, and a self-report is precisely
what this method refuses everywhere else: it can be set to `built` by anyone,
at any time, with nothing to contradict it.

There is deliberately no `showcased` state. Showcasing is an *action* performed
on built work to get feedback, not a property the work acquires, and a flag
claiming it had happened could never be checked. Until showcase events are
recorded, `next` prompts for it in its action text rather than tracking it.

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

Scaffolding an `exploded-spec` also adds its ledger row — unimplemented, with
no verify command yet. Without it the project would fail its own checks the
moment a subsystem was scaffolded, since every exploded spec must appear in the
ledger exactly once.

### Failure modes

| Condition | Observable result |
|---|---|
| Name is not lowercase-hyphenated | Exits 2, explains the naming rule |
| Target file already exists | Exits 2, refuses; never overwrites |
| Template missing | Exits 2, names the expected template path |

## Open questions

- A slice document is a record of a delivery, so it is not rewritten when later
  work supersedes it — but nothing currently stops it contradicting present
  behaviour. It is handled by convention today: a note at the top naming what
  superseded it. A `superseded-by` field would make the relationship checkable,
  at the cost of bookkeeping on every slice that is never superseded.

## Invariants

- A scaffolded document passes `check` immediately, with no placeholders left in
  its frontmatter.
- `id` always equals the filename stem, so a document can be found from a
  reference and vice versa.

## Depends on

- Templates in `.sprout/templates/`, one per kind.
