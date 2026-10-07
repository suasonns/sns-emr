# SNS Clinical Architecture

**Status:** Active supporting architecture
**Authority level:** Product-architecture supplement. It does not replace external authority, either constitution, or workstream-specific authority.

## Core rules

- One clinical or operational concept has one authoritative persisted path, one editable owner, one validation authority, one calculation authority when computed, one export transformation, one readiness interpretation, and one audit model.
- Read-only displays must show provenance. Assessment findings, referral needs, orders, and plan-of-care actions remain distinct concepts.
- Blank does not mean normal. Historical evidence does not become current evidence automatically.
- Manual workflows must remain fully usable without AI. AI may extract and suggest, but may not independently assess, approve, determine eligibility, create orders, auto-document, or mark a system reviewed.

## Body Systems

Canonical identifiers and labels:

- `neurological`: Neurological
- `respiratory`: Respiratory
- `cardiovascular`: Cardiovascular
- `nutrition`: Nutrition
- `gastrointestinal`: Gastrointestinal
- `genitourinary`: Genitourinary
- `musculoskeletal`: Musculoskeletal
- `integumentary`: Integumentary
- `infection_immunological`: Infection / Immunological
- `endocrine`: Endocrine

All ten systems remain available. Diagnosis does not suppress systems.

Legacy compatibility is adapter-only:

- `integumentary` ↔ `skin`
- `infection_immunological` ↔ `infection`

## Ownership boundaries

- Neurological owns orientation and cognition.
- Respiratory owns dyspnea and oxygen.
- Cardiovascular owns edema.
- Nutrition owns intake and weight.
- Gastrointestinal owns bowel status.
- Genitourinary owns urinary status.
- Musculoskeletal owns gait, balance, transfers, and mobility.
- Integumentary owns skin integrity, wounds, pressure injuries, body-map wound markers, wound detail, and Braden.
- Infection / Immunological owns active infection.
- Endocrine owns diabetes.

Braden mobility does not complete Musculoskeletal review. Braden nutrition does not complete Nutrition review. A body-map marker provides location context and does not complete a wound record.

## Visit modes

- Admission / Comprehensive establishes a current baseline across all ten systems.
- Routine RN emphasizes current condition, change, intervention, response, and follow-up.
- Recertification emphasizes dated comparison, progression, persistent burden, and evidence gaps.

These purposes do not authorize automatic eligibility or completion logic.
