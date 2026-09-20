# ADR-003: Evidence-First Architecture

## Status

Accepted

## Context

There is a natural product-design pull toward showcasing polished
AI-generated narrative summaries as the primary user-facing output, since
they are impressive and easy to read. In a clinical/compliance context,
however, an unsourced narrative is a liability: it cannot be defended in
an audit, ADR response, or survey without a clear path back to the
original documentation.

## Decision

SNS EMR is an evidence discovery platform, not a document summarization
platform. Evidence is primary; narrative summary is secondary and always
subordinate to it.

Every future intelligence feature (Clinical, Eligibility, Compliance,
Narrative Intelligence) must remain capable of answering:

> "Show me where the chart says that."

## Consequences

- Product and UI decisions must default to surfacing evidence alongside
  or ahead of narrative text, not behind it.
- Narrative-generation features are evaluated against whether they
  preserve a one-click path to evidence, not just against readability or
  polish.
- This principle takes precedence over feature velocity when the two are
  in tension.
