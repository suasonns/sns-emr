# SNS CLINICAL WORKSPACE STANDARD

STATUS: GOVERNANCE RULE — ADOPTED. Established during the PR #170
(Draft, `suasonns-feature/update-recertification-toggle`) human-review
readiness audit's real-browser width-utilization review.

## 1. PRIMARY SUPPORTED ENVIRONMENTS

SNS must be designed and validated against the owner's actual production
environments. All five of the following are **primary** support targets
— none is an edge case:

1. **34-inch ultrawide monitor** — the owner's primary workstation. Used
   for design, validation, review, charting, testing, and workflow
   analysis. This is the **primary production workspace**, not an
   outlier.
2. 15-inch laptop
3. 13-inch laptop
4. iPad
5. iPhone

## 2. WHY LARGE MONITORS ARE A FIRST-CLASS TARGET

Large/ultrawide monitors exist to support readability, visibility,
simultaneous information review, reduced scrolling, reduced window
switching, and reduced strain during long clinical documentation
sessions (see `SNS_CLINICAL_READABILITY_STANDARD.md`). A control is not
defective merely because it renders wide on a wide display; width must
be evaluated by workflow impact, not by an arbitrary pixel ceiling.

## 3. REQUIRED VALIDATION MATRIX

Every major clinical UI must be validated at minimum across the
viewport matrix defined in `SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md`
(ultrawide 3440, desktop 1920/1440, laptop 1366/1280, tablet 1024, phone
430/390), covering all five supported environments in §1.

## 4. SCOPE

Applies to all current and future SNS clinical screens, including but
not limited to: RNICA, Body Systems Registry, BodyShieldShell,
Neurological, Respiratory, Cardiovascular, Integumentary, Review By
Exception, Nurse Review, Admissions, Recertifications, and general
clinical workspace layouts.

## 5. RELATED STANDARDS

- `docs/governance/SNS_CLINICAL_READABILITY_STANDARD.md`
- `docs/governance/SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md`
- `docs/governance/SNS_PLAYWRIGHT_VALIDATION_STANDARD.md`

## 6. PROVENANCE

Adopted during the PR #170 real-browser width-utilization audit
(`suasonns-feature/update-recertification-toggle`, Draft). Does not
authorize any redesign of clinical fields, validation, response values,
or workflow behavior — see
`docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`
for the controlling scope boundary, which this rule does not relax.
