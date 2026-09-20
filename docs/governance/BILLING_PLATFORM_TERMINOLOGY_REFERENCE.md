# SNS HOSPICE SOLUTIONS — BILLING PLATFORM AUTHORITATIVE TERMINOLOGY REFERENCE

STATUS: APPROVED — LOCKED — SOURCE OF TRUTH

This document defines the approved user-facing terminology, internal
terminology, and prohibited terminology for the Billing Platform. When
a conflict exists, **Operational Billing Terminology** (this document)
takes precedence over generic terminology used elsewhere.

Use this document as the source of truth for: Figma, GitHub,
Discovery, Schema Design, Migration Design, Implementation Planning,
UI Labels, Reports, Exports, and Validation Rules. Any future
terminology changes require architectural review and approval — this
document does not itself authorize schema, migration, API, or UI
implementation for any Billing Platform feature; it governs naming
only, wherever and whenever such implementation is separately
authorized.

---

## 1. PAYER CATEGORIES

| Internal value (`claim_category`, Section 20.9 of `BILLING_ORGANIZATION_DISCOVERY_REPORT.md`) | User-facing label | Status |
|---|---|---|
| `MEDICARE_HOSPICE` | **Medicare Part A Hospice** | APPROVED |
| `MEDICAID` | Medicaid | APPROVED |
| `MEDI_CAL` | Medi-Cal | APPROVED |
| `MEDICARE_ADVANTAGE_HMO` | Medicare Advantage HMO | APPROVED |
| `MEDICARE_ADVANTAGE_PPO` | Medicare Advantage PPO | APPROVED |
| `COMMERCIAL_HMO` | Commercial HMO | APPROVED |
| `COMMERCIAL_PPO` | Commercial PPO | APPROVED |
| `COMMERCIAL_POS` | Commercial POS | APPROVED |
| `TRICARE` | TRICARE | APPROVED |
| `VETERANS_AFFAIRS` | Veterans Affairs (VA) | APPROVED |
| `PRIVATE_PAY` | Private Pay | APPROVED |
| `OTHER` | Other | APPROVED |

**Rationale (`MEDICARE_HOSPICE` → "Medicare Part A Hospice"):** hospice
claims are billed under the Medicare Part A Hospice Benefit. Using
only "Medicare Hospice" introduces ambiguity with Medicare Part A,
Medicare Part B, and Medicare Advantage. The Billing Platform must use
"Medicare Part A Hospice" for operational clarity. This is the same
decision already locked in `BILLING_ORGANIZATION_DISCOVERY_REPORT.md`
Section 28 — this document is now the primary authoritative source for
it; Section 28 remains valid and cross-references here.

## 2. COVERAGE ASSIGNMENTS

**Approved:** "Coverage Assignment"
**Not:** "Role"

**Rationale:** Coverage Assignment supports payer-specific work
ownership and future payer expansion. Examples: Medicare Biller,
Medi-Cal Biller, Managed Care Biller, VA Biller, Room & Board
Specialist. This governs **user-facing terminology only** — it does
not require renaming the internal `coverage_role` discriminator
already designed in `BILLING_ORGANIZATION_DISCOVERY_REPORT.md` Section
21.2, consistent with this document's internal-vs-user-facing
distinction principle (Section 1 above).

## 3. ACCESS MANAGEMENT

**Approved:** "Access Administration" — manage user access, capability
assignments, agency visibility, and access reviews.

**Prohibited:** "Credential Management," "Clearinghouse Credential
Administration," "Password Management," "Token Management" — consistent
with the existing "do not expose credentials/passwords/tokens" rules
already locked for User Access Detail (Section 27 of the discovery
report) and DDE authorization (Section 18.15/21.12).

## 4. USER ACCESS

**Approved:** "Billing Role Profile"
**Not:** "Employment Info"

**Rationale:** the Billing Platform is not an HR system — consistent
with every prior "no HR functionality" implementation boundary in this
report series.

## 5. CAPABILITY SOURCES

**Approved values:** Role Grant, Individual Grant, User-Specific
Grant, Not Granted.

**Important distinction:** *Source* explains **why** access exists.
*Granted By* identifies **who** approved the access. Source ≠ Granted
By — these remain two separate fields, consistent with
`BILLING_ORGANIZATION_DISCOVERY_REPORT.md` Section 27.3's planned
`source` and `granted_by_user_id` columns.

**Cross-reference to Section 27.11.1 (open question):** this document
confirms all four terms — Role Grant, Individual Grant, User-Specific
Grant, and Not Granted — are independently approved terminology, which
resolves the naming half of that open question (these are not simply
two names for one value; both "Individual Grant" and "User-Specific
Grant" are distinct, approved labels). It does **not** yet specify the
mechanical/storage distinction between "Individual Grant" and
"User-Specific Grant" (e.g. whether one is an admin-applied override
and the other a user-specific derivation rule) — that schema-level
question remains open and is not resolved by this terminology
reference, which governs naming, not data modeling.

## 6. DDE AUTHORIZATION

**Approved states:** Authorized, Not Authorized, Pending, Suspended,
Expired, Not Required — an exact match to the six values already
documented in `BILLING_ORGANIZATION_DISCOVERY_REPORT.md` Section
18.15/27.2; no new vocabulary introduced.

**Approved language:** "DDE Authorization Reviewed," "Authorization
status updated following approved review process."

**Prohibited:** display of DDE credentials, DDE usernames, DDE
passwords, MFA information — consistent with the existing "no DDE
credential storage/display" boundary.

## 7. SECURITY TERMINOLOGY

**Approved:** "Emergency Access"
**Optional supporting term:** "Break-Glass Event"

**Prohibited:** "Universal Access," "Super Admin Override," "Security
Bypass," "Clearance Level."

## 8. SECUREINBOX

**Approved:** "SecureInbox Routing Preview" — status "Coming Soon."

**Prohibited:** representing SecureInbox as operational or
implemented — consistent with the locked
`docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` (SecureInbox
remains future functionality; the Routing Preview stays display-only).

## 9. AUDIT LANGUAGE

**Approved:** "Audit Event," "Access Review," "Assignment History,"
"Configuration History," "Export History," "Append-Only," "Immutable."

**Prohibited:** "Delete Audit History," "Modify Audit History,"
"Rewrite Audit History" — consistent with the append-only audit design
already locked across Sections 18.18/21.9/25.7 of the discovery
report.

## 10. SETTINGS VS. OPERATIONS

**Approved distinction:** Settings configures behavior; operational
modules perform work.

**Settings includes:** Configuration, Defaults, Rules, Policies,
Integrations, Feature Availability.

**Operational modules include:** Claims, Denials, Appeals,
Eligibility, Payment Posting, Room & Board Operations, Agency Coverage
& Workload.

## 11. BILLING ORGANIZATION VS. SETTINGS

**Billing Organization owns:** Organization & Teams, Agency Coverage &
Workload, Access Administration.

**Settings owns:** General, Agency Billing, Payers & Plans, Claims
Settings, Clearinghouse, Payments & ERA, DDE Policy, Room & Board
Settings, Reports & Exports, Notifications, Security, Audit &
Retention, Integrations, Feature Configuration.

This is a new, explicit module-boundary statement: the payer-category
label mapping in Section 1 above lives under **Settings → Payers &
Plans** (per `settings-payers-plans-dark.png`), not under Billing
Organization — Billing Organization's own pages (Organization & Teams,
Agency Coverage & Workload, Access Administration, User Access Detail)
consume/display these labels but do not own their configuration.

## 12. CLINICAL TERMINOLOGY RESTRICTION

**Prohibited inside Billing Platform Settings:** clinical visit
density, clinical routing, clinical scheduling, clinical workload
optimization, patient care assignments.

**Approved replacement terms:** billing coverage ownership, agency
assignment coverage, workload visibility.

---

## RELATIONSHIP TO OTHER DOCUMENTS

This document governs terminology only. It does not replace or modify:
- `docs/biller-platform/BILLING_ORGANIZATION_DISCOVERY_REPORT.md`
  (data-model discovery, schema design, and migration design for
  Billing Organization — internal value lists such as `claim_category`
  in Section 20.9 remain authoritative for what is stored; this
  document is authoritative for what is displayed).
- `docs/governance/THEME_SYSTEM_REQUIREMENTS.md` (visual/theme
  parity — orthogonal to terminology).
- `docs/governance/SNS_DESIGN_SYSTEM_REFERENCE.md` (visual baseline
  from approved Figma references — orthogonal to terminology).
- `docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` (SecureInbox
  status, consistent with Section 8 above).

## FINAL STATUS

Billing Platform Terminology: **APPROVED — LOCKED — AUTHORITATIVE
REFERENCE.** Documentation only; no schema, migration, model, service,
route, or UI component created or changed as a result of this document.
