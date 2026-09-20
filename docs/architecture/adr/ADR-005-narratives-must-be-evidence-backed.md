# ADR-005: Narratives Must Be Evidence-Backed

## Status

Accepted

## Context

Future Narrative Intelligence work will generate admission summaries,
IDG summaries, LCD summaries, HOPE summaries, RN ICA summaries, ADR
review summaries, and recertification narratives. Without an explicit
rule, narrative generation could produce fluent statements that are not
individually traceable to the evidence that supports them — precisely
the failure mode the rest of this architecture is designed to prevent.

## Decision

Every narrative statement produced by any current or future summary
module must link back to its supporting evidence. Narrative statements
without a reachable evidence trail are prohibited from being generated
or displayed.

If a narrative statement synthesizes multiple pieces of evidence, all
contributing sources must be individually reachable from that statement,
not merged into a single, unattributed citation.

## Consequences

- Narrative Intelligence (Phase 6/7 in the roadmap documents) cannot ship
  independently of Evidence Traceability (Phase 2) — it is a downstream
  consumer, not a parallel capability.
- Any narrative-generating feature must be reviewed for this property
  before release: can every sentence be traced back to document, page,
  date, and excerpt?
- This rule applies uniformly across all named summary modules and any
  future ones added to the platform.
