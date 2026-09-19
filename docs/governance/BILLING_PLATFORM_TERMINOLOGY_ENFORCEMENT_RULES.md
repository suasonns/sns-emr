# GITHUB IMPLEMENTATION RULES — AUTHORITATIVE TERMINOLOGY ENFORCEMENT

STATUS: APPROVED — LOCKED — REQUIRED FOR ALL NEW DEVELOPMENT

## PURPOSE

This document defines how the terminology locked in
`docs/governance/BILLING_PLATFORM_TERMINOLOGY_REFERENCE.md` (the
"Authoritative Terminology Reference") must be implemented — and, just
as importantly, what must never be substituted — across UI, APIs,
Reports, Exports, Audit Events, Validation Logic, Documentation,
Tooltips, and Notifications. Figma is complete; GitHub must implement
using the approved terminology only. No terminology substitutions are
authorized. This document does not itself authorize any schema,
migration, API, or UI implementation — it governs what terminology
must be used *when and if* such implementation is separately
authorized, and defines the QA gate that implementation must pass.

## RULE 1 — INTERNAL VALUES ≠ USER-FACING LABELS

Internal system values may differ from UI labels (e.g. internal
`MEDICARE_HOSPICE` → user-facing "Medicare Part A Hospice"). This is
intentional. Do not rename UI labels to match enum names. Do not
rename enums to match UI labels.

## RULE 2 — MEDICARE PART A HOSPICE

Approved user label: **Medicare Part A Hospice**. Approved internal
value: `MEDICARE_HOSPICE`.

**Prohibited replacements:** "Medicare Hospice," "Medicare A,"
"Hospice Medicare," "Medicare Part A" (without "Hospice").

## RULE 3 — COVERAGE ASSIGNMENT

Approved: "Coverage Assignment." Prohibited: "Role" when describing
payer responsibility (e.g. "Coverage Assignment: Medicare Biller," not
"Role: Medicare Biller").

## RULE 4 — BILLING ROLE PROFILE

Approved: "Billing Role Profile." Prohibited: "Employment Info,"
"Employee Information," "HR Profile."

## RULE 5 — CAPABILITY GRANTS

Approved sources: Role Grant, Individual Grant, User-Specific Grant,
Not Granted. **Source is not Granted By** — GitHub must preserve both
fields distinctly (per `BILLING_ORGANIZATION_DISCOVERY_REPORT.md`
Section 27.3's planned `source` and `granted_by_user_id` columns).

## RULE 6 — DDE AUTHORIZATION

Approved states: Authorized, Not Authorized, Pending, Suspended,
Expired, Not Required. Approved activity label: "DDE Authorization
Reviewed."

**Prohibited:** "DDE Credential Verified," "External Utility
Verified," "CMS Utility Verified."

## RULE 7 — SECURITY TERMINOLOGY

Approved: "Emergency Access." Optional supporting term: "Break-Glass
Event."

**Prohibited:** "Super Admin Override," "Security Bypass," "Universal
Access," "Clearance Level."

## RULE 8 — ACCESS ADMINISTRATION

Approved description: "Manage user access, capability assignments,
agency visibility, and access reviews."

**Prohibited description content:** anything involving credential
management, password administration, token management, or secret
management.

## RULE 9 — FEATURE CONFIGURATION

Approved description: "Route billing coverage ownership, monitor
agency assignment coverage, and support workload visibility."

**Prohibited:** "Clinical routing," "Clinical scheduling," "Clinical
workforce optimization," "Clinical visit density."

## RULE 10 — SECUREINBOX

Approved: "SecureInbox Routing Preview." Status: "Coming Soon."

**Prohibited:** representing SecureInbox as operational or
implemented.

## RULE 11 — SETTINGS BOUNDARY

Settings configures behavior; operational modules perform work. GitHub
must not duplicate operational workflows, operational queues, or
workforce management inside Settings.

## RULE 12 — AUDIT TERMINOLOGY

Approved: "Audit Event," "Access Review," "Assignment History,"
"Configuration History," "Export History," "Append-Only," "Immutable."

**Prohibited:** "Delete Audit," "Modify Audit," "Rewrite Audit."

## RULE 13 — UNAUTHORIZED ACCESS

Approved: "Access Denied," "Required Capability," "Current Access,"
"Request Access," "Reference ID."

**Prohibited:** "Clearance Level Required," "Level 1"/"Level
2"/"Level 3"/"Level 4," "Security Clearance."

## RULE 14 — PAYER CATEGORY LABELS

Approved user-facing labels (exhaustive — do not invent alternates):
Medicare Part A Hospice, Medicaid, Medi-Cal, Medicare Advantage HMO,
Medicare Advantage PPO, Commercial HMO, Commercial PPO, Commercial
POS, TRICARE, Veterans Affairs (VA), Private Pay, Other.

---

## TERMINOLOGY QA CHECKLIST (GITHUB ONLY)

Run before: PR Approval, Merge, Release, Demo, UAT.

**UI QA**
- [ ] Medicare Part A Hospice used everywhere.
- [ ] Coverage Assignment used everywhere.
- [ ] Billing Role Profile used everywhere.
- [ ] Access Administration description matches approved wording.
- [ ] Feature Configuration description matches approved wording.
- [ ] Emergency Access used instead of clearance terminology.
- [ ] SecureInbox marked Coming Soon.
- [ ] DDE Authorization Reviewed wording used.

**API QA**
- [ ] Internal enums remain unchanged.
- [ ] API contracts use internal values.
- [ ] UI labels do not leak into API values.
- [ ] API values do not leak into UI labels.

**Report QA**
- [ ] Reports display approved labels.
- [ ] Exports display approved labels.
- [ ] Audit reports display approved labels.
- [ ] No alternate payer terminology introduced.

**Documentation QA**
- [ ] Discovery documents use approved terminology.
- [ ] Schema documents use approved terminology.
- [ ] Migration documents use approved terminology.
- [ ] Implementation guides use approved terminology.
- [ ] Test plans use approved terminology.

**Security QA**
- [ ] No credential-management language appears in Access Administration.
- [ ] No clinical terminology appears in Billing Settings.
- [ ] No clearance-level language appears anywhere.
- [ ] No SecureInbox operational claims appear.

---

## FAIL CONDITIONS

Reject the PR if any of the following appear:
- [ ] "Medicare Hospice"
- [ ] "Employment Info"
- [ ] "Role" (used in place of "Coverage Assignment")
- [ ] "Clearance Level"
- [ ] "Security Clearance"
- [ ] "Clinical Visit Density"
- [ ] "Credential Management" inside Access Administration
- [ ] SecureInbox presented as operational

---

## FINAL RULE

If a label differs from the Authoritative Terminology Reference
(`docs/governance/BILLING_PLATFORM_TERMINOLOGY_REFERENCE.md`): **DO
NOT IMPLEMENT.** Request terminology review first. The Authoritative
Terminology Reference remains the source of truth.

## STATUS

Documentation only. No schema, migration, model, service, route, or UI
component created or changed as a result of this document. This
enforcement checklist governs review/merge gating for terminology
whenever implementation is separately authorized — it does not itself
authorize implementation.
