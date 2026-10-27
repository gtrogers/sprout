---
name: sprout-spike
description: Investigate one focused technical unknown under a timebox and distil the result into a one-page reference doc. Use when the user asks for a spike or investigation, or when a spec, interface or build loop is blocked on something genuinely unknown - for example how to write native macOS apps in Odin.
---

# Spike

A short, focused investigation whose output is a one-page reference someone can
act on. The deliverable is the distillation, not the investigation.

## Invariant

One question, timeboxed, one page.

A spike that grows a second question has become two spikes. A spike without a
timebox becomes the project. Agree the box up front — "an hour", "twenty tool
calls", "until we know whether X is possible" — and respect it.

## Enter when

A decision is blocked on something genuinely unknown, and guessing would be
expensive. Good triggers: an unfamiliar platform, library or language; whether
an approach is viable at all; which of two options survives contact.

Not a spike: something the docs answer directly, a question about code already
in the repo, or a decision that is really a preference. Say so and move on.

Scaffold with `python3 .sprout/sprout.py new spike <name>`.

## Loop

Write the question down first, as one sentence, with the decision it blocks.
If you cannot, you are not ready to investigate.

Each pass:

1. **Investigate the smallest thing** that would move the answer. Prefer
   running code over reading about it — a twenty-line program that compiles
   settles more than an hour of documentation.
2. **Record traps as you hit them**, not afterwards. Time lost to a trap is the
   most valuable thing a spike produces and the first thing forgotten.
3. **Ask: can I now answer the question well enough to decide?**
   - Yes → exit and distil
   - No, but I know what to try next → go round again
   - No, and I am no longer sure what the question is → the question was too
     broad. Narrow it and restate it

Stop when the box is spent, even unanswered. "We spent an hour and here is how
far we got" is a legitimate, useful outcome. Pretending otherwise is not.

## Then distil

Rewrite, do not append. The reader wants what to do, not what you tried.

Work `.sprout/templates/spike.md`:

- **Verdict** first, in two or three sentences. A reader who stops there can
  still act.
- **What you need to know** — the minimum working knowledge. Prefer a small
  example that actually runs over prose describing one.
- **Traps** — the highest-value section, and the most often skipped.
- **Rejected alternatives** — so this is not relitigated in three weeks.
- **Consequences for the spec** — what the overview or an exploded spec should
  now say. A spike that changes nothing upstream was not needed.

Keep it under roughly 150 lines. Delete your working notes; they are not the
artifact.

## Exit — success

- The question is answered, or the box is spent and the state of knowledge is
  honestly recorded
- Verdict stands alone and is actionable
- Traps are written down
- Consequences for the spec are named, and applied via `sprout-spec` or
  `sprout-slice` if they matter
- Fits on a page; working notes removed
- `python3 .sprout/sprout.py check` passes

Then: back to whatever was blocked.

## Exit — failure

- **The question was too broad.** Two narrowings and it still will not resolve.
  Split it into separate spikes and run the one that unblocks the most.
- **The answer is "this approach does not work".** A successful spike, not a
  failed one. Write it up with the same care — a well-documented dead end saves
  the next person the whole trip.
- **It is turning into implementation.** You are building the thing rather than
  answering the question. Stop, write up what you know, throw the code away,
  and re-enter `sprout-slice` properly. Spike code is evidence, never a
  foundation.
