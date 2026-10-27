---
id: {{id}}
kind: spec
version: 1
status: draft
---

# {{title}}

> The overview spec. Goals and intent, not implementation. If a reader could
> build this three different ways and all three would satisfy you, the spec is
> at the right altitude.

## Problem

What is wrong with the world right now, for whom. Two or three sentences.

## Goals

What success looks like, stated as outcomes rather than features.

- 
- 

## Non-goals

What this deliberately will not do. This section prevents more rework than any
other, so be specific and slightly uncomfortable.

- 
- 

## Subsystems

The parts this naturally decomposes into. Name and one-line purpose only — each
gets its own exploded spec when a slice touches it. Aim for 3–7; more than that
usually means the boundaries are wrong.

| Subsystem | Purpose |
|---|---|
|  |  |

## Constraints

Technical and product constraints that are *given*, not chosen. Platform,
language, dependency limits, performance floors, regulatory, deadline.

- 
- 

## Invariants

Properties that must hold at every commit, not just at the end. These become
the things worth writing checks for.

- 
- 

## Open questions

Unknowns that could change the shape of the thing. A question here is a
candidate for a spike.

- 
