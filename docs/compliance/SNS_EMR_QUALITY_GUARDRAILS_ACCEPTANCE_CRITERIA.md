
# SNS EMR — Quality Guardrails: Engineering Acceptance Criteria (Tied to Plan)

**Source:** `SNS_EMR_QUALITY_GUARDRAILS_PLAN.md`  
**Goal:** Implement guardrails without disrupting care and without punitive enforcement.

---

## A) Functional Acceptance Criteria

### A1. Authoritative Time-In/Time-Out
- **Given** a visit/encounter is created,
- **When** staff enters time_in and time_out,
- **Then** the system calculates duration from those values and treats them as authoritative.
- **And** AI capture start/stop (if present) never changes authoritative duration.

### A2. Multiple Same-Day Visits Allowed
- **Given** a patient has one finalized visit on a day,
- **When** a second (or third) visit is created on the same day,
- **Then** the system allows creation, documentation, and finalization without blocks.

### A3. No Hard Minimum Duration Enforcement
- **Given** a visit duration is less than a tenant’s “expected” threshold,
- **When** the visit is finalized,
- **Then** the system does not block finalization.

### A4. Soft QA Prompt (Non-blocking)
- **Given** a visit duration is below a tenant-configured “short visit” threshold,
- **When** staff attempts to finalize,
- **Then** the system may show a reminder prompt,
- **And** staff can proceed without additional required actions.

### A5. Tenant Toggle Behavior
- **Given** `quality.philosophy.enabled = OFF`,
- **Then** the quality philosophy statement is not shown anywhere.

- **Given** `quality.philosophy.enabled = ON`,
- **Then** the statement appears only in leadership contexts:
  - QAPI review screens
  - Survey readiness views
  - QA context panels
- **And** it never appears in bedside visit note UI.

### A6. Locked Statement Integrity
- **Given** the quality philosophy statement is displayed,
- **Then** it is the exact locked text and cannot be edited by tenants.

---

## B) Security / Access Acceptance Criteria

### B1. Role-based visibility
- Only users with QAPI/Leadership permissions can view QAPI dashboards.
- Bedside staff do not see organizational philosophy messaging.

### B2. Tenant isolation
- All QAPI dashboards are tenant-scoped.

---

## C) Compliance / Audit Acceptance Criteria

### C1. Documentation credibility preserved
- The system must support documenting visits that prioritize patient care first (documentation may occur after care).

### C2. Continuous Care support (non-blocking)
- The system supports multiple disciplines in the same day and stores their times.

---

## D) Automated Test Acceptance Criteria

- Unit tests exist for:
  - duration from time_in/time_out
  - AI timing does not override duration
  - multiple same-day visits allowed
  - toggle on/off visibility

- Compliance tests exist to ensure:
  - no hard stops on duration
  - statement is never injected into clinical notes

---

## E) Non-Functional Acceptance Criteria

- Performance: QAPI dashboards load within acceptable response time for 30-day and 90-day ranges.
- Reliability: toggles are cached safely per-tenant (no cross-tenant leakage).
- Maintainability: statement text is stored as a constant/seeded record and referenced by ID.

