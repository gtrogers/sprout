---
id: {{id}}
kind: exploded-spec
version: 1
status: draft
parent: overview
---

# {{title}}

> One subsystem, exploded from the overview spec for a specific slice. Intent
> and interface only. Anything a unit or end-to-end test could pin down belongs
> in a test, not here.

## Purpose

What this subsystem is responsible for, in one or two sentences. If you need
"and" more than once, it is probably two subsystems.

## Responsibilities

- 

## Explicitly not responsible for

Where this subsystem's duties stop, and who picks them up.

- 

## Interface

How the rest of the system talks to this. Shapes and contracts, not signatures
you have already written. Describe what callers may rely on.

### Inputs

| Name | Shape | Meaning |
|---|---|---|
|  |  |  |

### Outputs

| Name | Shape | Meaning |
|---|---|---|
|  |  |  |

### Failure modes

What can go wrong and what the caller observes when it does. Callers depend on
failure behaviour as much as success behaviour, so it is part of the interface.

| Condition | Observable result |
|---|---|
|  |  |

## Invariants

What is always true of this subsystem, regardless of call order or input.

- 

## Depends on

Other subsystems this needs, and what it needs from them.

- 

## Open questions

- 
