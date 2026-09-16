# ADR-002: Evidence Traceability Required

## Status

Accepted

## Context

AI-generated findings and summaries are only trustworthy in a regulated
hospice/EMR context if a clinician or auditor can verify exactly where
each statement came from. Without enforced traceability, future features
could ship findings or narrative statements that are not independently
verifiable, which is unacceptable for compliance, audit, and ADR
response scenarios.

## Decision

Every finding produced by the evidence platform must remain capable of
linking back to:

- Source document
- Document date
- Document type
- Page number (when available)
- Paragraph / line number (when available)
- Original/verbatim source excerpt
- Confidence score
- Extraction source

If richer locators (e.g. page coordinates) become available in the
future, they must be preserved and exposed, not discarded for
simplicity.

## Consequences

- Every future finding-producing service must carry these fields through
  its pipeline end-to-end.
- UI surfaces for findings/summaries must provide a path from any
  statement to this evidence trail.
- A finding lacking one or more of these fields must be visually flagged
  as unverified rather than presented as equivalent to a fully-sourced
  finding.
