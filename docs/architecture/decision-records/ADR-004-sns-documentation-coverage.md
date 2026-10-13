# ADR-004: SNS Documentation Coverage

## Status

Approved

## Date

2026-10-12

## Author

Product Owner (SNS Hospice Solutions)

## Origin

Documentation Coverage did not originate in Neurological. It originated
as a pilot concept during Respiratory review, where it existed to answer
a narrow, practical question: when an approved field creates a
downstream requirement (for example, Oxygen Use = Yes implying Oxygen
Flow Rate should be recorded), has that requirement actually been
documented, or is it still missing?

Neurological was the first system to expand and refine Coverage's
clinician-facing presentation model (per-item label + documented value,
or label + exact unresolved hint, instead of a flat checklist line). This
expansion did not change Coverage's purpose or create new ownership.
Neuro is one implementation of Coverage; Respiratory is another. Neither
system owns the architecture.

## Purpose

Documentation Coverage exists to answer exactly two questions for any
Body System:

1. What is documented?
2. What is missing?

Coverage reads the Body System's existing source fields, reports the
clinician's documented answer verbatim (including explicit negative
answers such as "None," "No Current Concern," or "Unable to Assess,"
which count as documented, not missing), and — when an approved
requirement has no answer — reports the exact missing requirement (for
example, "Select comparison to prior assessment"), never a generic
"Incomplete."

## Ownership

Documentation Coverage belongs to the SNS Body-System Framework. It is
not a Neurological feature and not a Respiratory feature. Any Body
System may implement Coverage using its own source-field mappings and
item definitions; the contract and behavioral rules below apply
uniformly.

## Contract

Every Coverage item returned by any Body System's Coverage function must
conform to this shape, and no other fields may be added without a
superseding ADR:

```
{
  key,
  label,
  complete,
  value,
  unresolvedHint,
  sourceFieldKeys
}
```

- `value` is populated only when `complete` is true; it is never
  fabricated for an incomplete item.
- `unresolvedHint` is populated only when `complete` is false, and must
  state the exact missing requirement, not a generic placeholder.
- `sourceFieldKeys` identifies the underlying Body-System field(s) the
  item reads, for traceability.
- A retired field (per the Retired Feature Registry) must never appear
  as a Coverage item or as an unresolved requirement.

## Explicitly Rejected Concepts

The following concepts are not part of Documentation Coverage and must
not be added without a superseding ADR:

- AI-generated or AI-validated Coverage content
- A general clinical-validation or finding-validation framework
- Supported / unsupported finding states
- Corroborated / uncorroborated states
- Clarification-needed states
- Insufficient-support states
- Resolved / unresolved (interdisciplinary) states
- An IDG (Interdisciplinary Group) review framework
- Any requirement that Coverage prove a Structured Finding was generated
  before counting a documented answer as complete

These concepts may be considered in a future, separate interdisciplinary
or AI-assisted review architecture, but they do not belong in
Documentation Coverage.

## Consequences

- Any future Body System adopting Coverage (Respiratory, Cardiovascular,
  GI, Infection, GU, Skin, Musculoskeletal, Safety, or others) must use
  the contract above with system-specific source-field mappings; it must
  not inherit Neuro-specific behavior (its 7-item definition, its
  `computeNeurologicalSystemStatus` alias/consumer wiring, or its
  specific CSS layout) merely because Neuro was the first expanded
  implementation.
- Any proposal to add a new Coverage state or field must reference this
  ADR and explain why the existing contract is insufficient, before any
  code is written.
- This ADR does not retire or replace Neurological Overview
  (`deriveNeurologicalOverview`); that remains a separate, system-status
  concern outside Coverage's scope.

## Related

- ADR-001 — RNICA Baseline
- `sns-emr-frontend/src/components/RNICA.jsx` —
  `computeNeurologicalDocumentationCoverage` (first expanded
  implementation of this contract)
- `docs/governance/SNS_RETIRED_FEATURES.json` — Retired Feature Registry
  referenced by the retirement-protection rule above
