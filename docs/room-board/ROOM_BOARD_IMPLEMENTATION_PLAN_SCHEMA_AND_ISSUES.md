THIS DOCUMENT REPLACES THE EARLIER FACILITY COLLECTIONS IMPLEMENTATION BRIEF.

DO NOT IMPLEMENT THE FORMER FACILITY COLLECTIONS OR CONTRACT RECOVERY MODEL.

==================================================
ROOM & BOARD BILLING, REIMBURSEMENT,
AND FINANCIAL RECONCILIATION
==================================================

STATUS

APPROVED

FIGMA LOCKED

IMPLEMENTATION PLANNING AUTHORIZED

==================================================
CRITICAL PLATFORM SEPARATION
==================================================

THIS IS ONE SHARED ROOM & BOARD DOMAIN WITH TWO DISTINCT PLATFORMS.

PLATFORM A

SNS Tech Solutions
Biller Platform

Page:

Room & Board Billing & Reimbursement Center

Purpose:

- Prepare monthly Room & Board billing
- Submit claims to Medi-Cal or responsible managed care plans
- Track payer responses
- Record exact reimbursements
- Allocate remittances to patients and service months
- Manage missing, delayed, partial, short-paid, rejected, and denied reimbursement
- Create payer follow-up, dispute, and appeal work

--------------------------------------------------

PLATFORM B

SNS Hospice Solutions
Tenant Platform

Page:

Room & Board Financial Reconciliation Center

Purpose:

- Track SNF obligations
- Track exact payments issued to SNFs
- Track hospice-funded pass-through advances
- Reconcile SNF payments with payer reimbursement
- Monitor reimbursement and payable aging
- Support agency financial reporting
- Produce annual Room & Board reconciliation support schedules

--------------------------------------------------

SHARED DOMAIN RULE

Both platforms must use the same authoritative records.

DO NOT create separate copies of:

- Room & Board cases
- Service periods
- Claims
- Payer remittances
- Payment allocations
- SNF payables
- SNF payments
- Hospice-funded advances
- Reconciliation records
- Evidence
- Audit events

Biller Platform permissions do not become Tenant Platform permissions.

Tenant Platform permissions do not become Biller Platform permissions.

Each API request must enforce:

- Authentication
- Platform permission
- Tenant or agency scope
- Billing assignment when applicable
- Action-specific permission

==================================================
VERIFY-FIRST REQUIREMENT
==================================================

The schema names in this document are logical target names.

They are not permission to create duplicate tables.

Before implementation:

1. Inspect existing repository models.
2. Inspect current migrations and Alembic head.
3. Inspect tenant and agency models.
4. Inspect patient and facility models.
5. Inspect payer and coverage models.
6. Inspect claims and remittance models.
7. Inspect payment-posting infrastructure.
8. Inspect work-item infrastructure.
9. Inspect document and evidence infrastructure.
10. Inspect audit-event infrastructure.
11. Classify each logical entity as REUSE, EXTEND, or CREATE.
12. Document exact repository evidence.

Do not create migrations before discovery is reviewed.

Do not use alembic stamp.

Do not rewrite historical migrations.

Do not create schema drift.

Use only reviewed, forward-only migrations.

==================================================
EPIC
==================================================

TITLE

Implement Shared Room & Board Billing and Financial Reconciliation Domain

LABELS

- biller-platform
- tenant-platform
- room-and-board
- medi-cal
- reimbursement
- financial-reconciliation
- compliance
- audit
- high-priority
- figma-locked

EPIC ACCEPTANCE

□ One authoritative Room & Board domain exists.

□ Biller and Tenant pages use the same records.

□ Biller and Tenant permissions remain separated.

□ Exact payer payment amount is recorded.

□ Exact payer payment date is recorded.

□ Payer payments can be allocated across service periods.

□ Exact SNF payment amount is recorded.

□ Exact SNF payment date is recorded.

□ Hospice-funded advances are calculated.

□ Patient and service-month reconciliation is available.

□ Reimbursement and SNF liability aging remain separate.

□ Annual reporting support schedule is available.

□ History is immutable.

□ Tenant isolation is verified.

□ Both pages match approved Figma.

==================================================
MILESTONE 0
REPOSITORY DISCOVERY AND MODEL MAPPING
==================================================

GITHUB ISSUE 0.1

TITLE

[Room & Board] Discover existing repository models and integration points

TASKS

□ Locate tenant and agency models.

□ Locate patient and census models.

□ Locate facility and facility-agreement models.

□ Locate payer, plan, eligibility, and coverage models.

□ Locate existing billing-period and service-period models.

□ Locate claim and claim-lifecycle models.

□ Locate ERA, remittance, payment, and allocation models.

□ Locate SNF payable or accounts-payable structures.

□ Locate work-item and queue structures.

□ Locate evidence and document references.

□ Locate audit-event structures.

□ Locate export and financial-report infrastructure.

□ Locate Biller Platform authorization.

□ Locate Tenant Platform authorization.

□ Locate Figma target routes and components.

DELIVERABLE

/docs/room-board/ROOM_BOARD_DISCOVERY_REPORT.md

DISCOVERY MATRIX

For every logical entity document:

- Logical Entity
- Existing Model
- Existing Table
- Existing Fields
- Existing Relationships
- Existing Constraints
- Existing Indexes
- Existing Service
- Existing Endpoint
- Existing UI
- Decision: REUSE, EXTEND, or CREATE
- Reason
- Files Affected
- Migration Required
- Verification Evidence

ACCEPTANCE

□ Every logical entity is classified.

□ Current migration revision is recorded.

□ Expected migration head is recorded.

□ ORM and database alignment is verified.

□ No unresolved schema drift exists.

□ No duplicate architecture is proposed.

□ Biller and Tenant authorization paths are identified.

BLOCKER

No schema, migration, or implementation work may proceed until Issue 0.1 passes.

==================================================
MILESTONE 1
SHARED ROOM & BOARD DOMAIN FOUNDATION
==================================================

GITHUB ISSUE 1.1

TITLE

[Room & Board] Implement or extend Room & Board case foundation

PURPOSE

Create the master association among:

- Tenant agency
- Patient
- Facility
- Responsible payer
- Hospice election
- Room & Board eligibility period
- Governing agreement
- Applicable rate source

TASKS

□ Reuse or implement RoomBoardCase.

□ Link the case to one tenant agency.

□ Link the case to one patient.

□ Link the case to one facility.

□ Link the case to the responsible payer.

□ Link applicable coverage.

□ Link applicable facility agreement.

□ Record workflow applicability.

□ Record current master status.

□ Add version and audit support.

ACCEPTANCE

□ A case belongs to exactly one tenant agency.

□ Patient belongs to the same tenant agency.

□ Facility is authorized for the tenant context.

□ Payer responsibility is explicit.

□ Case applicability is recorded.

□ Historical status remains available.

□ A case cannot be physically deleted after financial activity exists.

--------------------------------------------------

GITHUB ISSUE 1.2

TITLE

[Room & Board] Implement patient service-period ledger

PURPOSE

Create the monthly or from-through billing unit used for claims, reimbursement, SNF payment, and reconciliation.

TASKS

□ Reuse or implement RoomBoardServicePeriod.

□ Support service month.

□ Support from and through dates.

□ Store eligible days.

□ Store expected reimbursement.

□ Store expected SNF obligation.

□ Store share of cost where applicable.

□ Store rate-source reference.

□ Store period status.

□ Prevent duplicate active periods.

ACCEPTANCE

□ Every period belongs to one Room & Board case.

□ Period end cannot precede period start.

□ Equivalent active periods cannot overlap unintentionally.

□ Monetary values use fixed-precision numeric types.

□ Service-period history remains available.

□ Period corrections use superseding versions.

==================================================
MILESTONE 2
ROOM & BOARD BILLING AND CLAIM LIFECYCLE
==================================================

GITHUB ISSUE 2.1

TITLE

[Biller Platform] Implement Room & Board claim preparation and validation

TASKS

□ Reuse or implement RoomBoardClaim.

□ Validate applicable patient coverage.

□ Validate facility residence.

□ Validate hospice election data.

□ Validate payer responsibility.

□ Validate agreement reference.

□ Validate service dates.

□ Validate expected-rate source.

□ Validate duplicate billing.

□ Validate previous submissions.

□ Present failed rules and resolution paths.

ACCEPTANCE

□ Blocked claims cannot enter Ready to Bill.

□ Validation result includes ruleset version.

□ Failed conditions identify owner and next action.

□ Passed with Warning remains distinct from Passed.

□ Revalidation creates a new result.

□ Previous validation remains preserved.

--------------------------------------------------

GITHUB ISSUE 2.2

TITLE

[Biller Platform] Implement Room & Board claim submission lifecycle

REQUIRED STATES

- Draft
- Validation Required
- Ready to Bill
- On Hold
- Submission Pending
- Submitted
- Submission Acknowledged
- Accepted for Processing
- Returned for Correction
- Rejected
- Denied
- Resubmission Required
- Resubmitted
- Payment Pending
- Billing Complete
- Cancelled Before Processing
- Superseded

TASKS

□ Implement server-controlled transitions.

□ Preserve every submission attempt.

□ Preserve clearinghouse or payer reference.

□ Support corrected submissions.

□ Support returned and rejected claims.

□ Support denial and appeal linkage.

□ Prevent destructive history changes.

ACCEPTANCE

□ Submitted does not mean accepted.

□ Accepted does not mean paid.

□ Rejected does not mean denied.

□ Original submission survives resubmission.

□ Invalid transitions are rejected.

□ Duplicate external acknowledgements are idempotent.

□ Out-of-order responses do not rewrite history.

==================================================
MILESTONE 3
PAYER REMITTANCE AND PAYMENT ALLOCATION
==================================================

GITHUB ISSUE 3.1

TITLE

[Shared Domain] Implement Room & Board payer remittance intake

TASKS

□ Reuse authoritative remittance infrastructure.

□ Record payer identity.

□ Record exact gross payment amount.

□ Record exact payment date.

□ Record exact receipt or deposit date where available.

□ Record check number or EFT trace.

□ Record remittance reference.

□ Record source type.

□ Store remittance evidence.

□ Prevent duplicate remittance ingestion.

ACCEPTANCE

□ Exact payment amount is preserved.

□ Exact payment date is preserved.

□ Payer source is preserved.

□ Duplicate EFT or check ingestion is prevented.

□ Reversal does not delete the original payment.

□ Unmatched remittance remains in a review queue.

--------------------------------------------------

GITHUB ISSUE 3.2

TITLE

[Biller Platform] Implement service-period payment allocation

PURPOSE

Allow one remittance to cover multiple:

- Patients
- Facilities
- Claims
- Service periods

REQUIRED STATES

- Unallocated
- Partially Allocated
- Fully Allocated
- Allocation Under Review
- Allocation Disputed
- Allocation Corrected
- Allocation Reversed

TASKS

□ Implement PaymentAllocation.

□ Support one remittance to many allocations.

□ Link allocation to service period.

□ Link allocation to patient.

□ Link allocation to facility.

□ Link allocation to claim when available.

□ Preserve allocated amount.

□ Preserve adjustment amount.

□ Preserve actor and date.

□ Support correction and reversal.

ACCEPTANCE

□ Allocated amounts cannot exceed available remittance unless explicitly supported by an approved adjustment rule.

□ Sum of active allocations is reproducible.

□ Partial allocation leaves an unallocated balance.

□ Allocation correction preserves original history.

□ Allocation reversal preserves original allocation.

□ Reconciliation does not treat unallocated money as payment for a service period.

==================================================
MILESTONE 4
SNF PAYABLES AND SNF PAYMENTS
==================================================

GITHUB ISSUE 4.1

TITLE

[Tenant Platform] Implement SNF payable obligations

REQUIRED STATES

- Obligation Not Established
- Facility Invoice Pending
- Facility Invoice Received
- Under Review
- Approved for Payment
- Payment Scheduled
- Partially Paid
- Paid in Full
- Payment on Hold
- Payment Disputed
- Adjustment Required
- Cancelled
- Closed

TASKS

□ Reuse or implement SNFPayable.

□ Link payable to service period.

□ Link payable to facility.

□ Link payable to patient.

□ Record facility invoice amount.

□ Record approved amount.

□ Record share of cost where applicable.

□ Record due date.

□ Record supporting agreement.

□ Record adjustment history.

ACCEPTANCE

□ Exact payable basis is traceable.

□ Approved amount is distinct from invoice amount.

□ Partial payment does not close the payable.

□ Cancellation requires reason and authority.

□ Historical payable versions remain available.

--------------------------------------------------

GITHUB ISSUE 4.2

TITLE

[Tenant Platform] Implement SNF payment ledger

REQUIRED STATES

- Not Paid
- Scheduled
- Payment Processing
- Partially Paid
- Paid in Full
- Payment Failed
- Payment Reissued
- Payment Voided
- Payment Reconciled

TASKS

□ Reuse or implement SNFPayment.

□ Record exact amount paid.

□ Record exact payment date.

□ Record check number or EFT reference.

□ Record payment method.

□ Record service period covered.

□ Record approving user.

□ Record posting user.

□ Preserve payment evidence.

□ Support void and reissue.

ACCEPTANCE

□ The agency can answer when the SNF was paid.

□ The agency can answer the exact amount paid.

□ Payment cannot exist without an approved payable or approved exception.

□ Payment void does not delete the original.

□ Reissued payment references the prior payment.

□ Payment cannot be recorded automatically by AI.

==================================================
MILESTONE 5
HOSPICE-FUNDED ADVANCE ENGINE
==================================================

GITHUB ISSUE 5.1

TITLE

[Shared Domain] Implement hospice-funded pass-through advance tracking

REQUIRED STATES

- No Advance
- Advance Open
- Partially Reimbursed Advance
- Fully Reimbursed Advance
- Advance Under Review
- Advance Disputed
- Advance Closed

CALCULATION

Hospice-Funded Advance is based on:

SNF payments issued for a service period
minus
payer reimbursement allocated to the same service period

The calculation must account for:

- Valid reversals
- Approved payer adjustments
- Approved facility adjustments
- Partial payments
- Corrected allocations

TASKS

□ Implement authoritative calculation service.

□ Calculate service-period advance.

□ Aggregate by patient.

□ Aggregate by facility.

□ Aggregate by payer.

□ Aggregate by tenant agency.

□ Preserve as-of timestamp.

□ Preserve calculation version.

ACCEPTANCE

□ Advance is not automatically labeled profit or loss.

□ One payment is not counted twice.

□ Unallocated payer money does not reduce an advance.

□ Voided SNF payments do not increase active exposure.

□ Partial reimbursement changes status correctly.

□ Fully allocated reimbursement can close the advance only after reconciliation requirements pass.

==================================================
MILESTONE 6
RECONCILIATION ENGINE
==================================================

GITHUB ISSUE 6.1

TITLE

[Shared Domain] Implement service-period financial reconciliation

REQUIRED STATES

- Not Ready for Reconciliation
- Reconciliation Pending
- In Reconciliation
- Matched
- Partial Match
- Payer Variance
- Facility Variance
- Missing Payer Payment
- Missing SNF Payment Record
- Duplicate Payment Suspected
- Adjustment Review Required
- Reconciled with Exception
- Fully Reconciled
- Reopened
- Closed

RECONCILIATION INPUTS

- Expected payer reimbursement
- Claimed amount
- Actual payer reimbursement allocated
- Payer adjustment
- SNF obligation
- Actual SNF payment
- Facility adjustment
- Outstanding payer reimbursement
- Outstanding SNF payable
- Hospice-funded advance

TASKS

□ Implement deterministic reconciliation service.

□ Implement variance classification.

□ Implement manual-review workflow.

□ Implement reconciliation closure.

□ Implement reopening.

□ Preserve calculation snapshot.

□ Preserve evidence.

ACCEPTANCE

□ Payer claim status remains independent.

□ Payer reimbursement status remains independent.

□ SNF payable status remains independent.

□ Reconciliation status remains independent.

□ Payment Received does not automatically mean Fully Reconciled.

□ SNF Paid does not automatically mean payer reimbursement was received.

□ Reopening requires reason and authority.

□ Historical reconciliation remains immutable.

==================================================
MILESTONE 7
BILLER PLATFORM API AND UI
==================================================

GITHUB ISSUE 7.1

TITLE

[Biller Platform] Implement Room & Board Billing & Reimbursement APIs

BASE ROUTE

Use repository routing conventions.

Logical route namespace:

/api/biller/room-board

Do not create this exact namespace if an authoritative versioned API convention already exists.

ENDPOINTS

GET /summary

Purpose:

Return Biller Platform Room & Board KPI summary.

Permission:

room_board.biller.view

--------------------------------------------------

GET /cases

Purpose:

List Room & Board cases for assigned agencies.

Permission:

room_board.biller.view

--------------------------------------------------

GET /cases/{case_id}

Purpose:

Return authorized case detail.

Permission:

room_board.biller.view

--------------------------------------------------

POST /cases/{case_id}/service-periods

Purpose:

Create a new monthly or from-through billing period.

Permission:

room_board.billing_period.create

--------------------------------------------------

POST /service-periods/{period_id}/validate

Purpose:

Run claim validation.

Permission:

room_board.claim.validate

--------------------------------------------------

POST /service-periods/{period_id}/claims

Purpose:

Prepare a claim.

Permission:

room_board.claim.create

--------------------------------------------------

POST /claims/{claim_id}/submit

Purpose:

Submit through approved configured integration.

Permission:

room_board.claim.submit

Additional requirement:

Human action required.

--------------------------------------------------

POST /claims/{claim_id}/hold

Permission:

room_board.claim.hold

--------------------------------------------------

POST /claims/{claim_id}/correct

Permission:

room_board.claim.correct

--------------------------------------------------

POST /claims/{claim_id}/resubmit

Permission:

room_board.claim.resubmit

--------------------------------------------------

GET /reimbursements

Purpose:

List reimbursement queue.

Permission:

room_board.reimbursement.view

--------------------------------------------------

POST /remittances

Purpose:

Record or import authoritative payer remittance.

Permission:

room_board.remittance.record

--------------------------------------------------

GET /remittances/{remittance_id}

Permission:

room_board.remittance.view

--------------------------------------------------

POST /remittances/{remittance_id}/allocations

Permission:

room_board.allocation.create

--------------------------------------------------

POST /allocations/{allocation_id}/correct

Permission:

room_board.allocation.correct

--------------------------------------------------

POST /allocations/{allocation_id}/reverse

Permission:

room_board.allocation.reverse

--------------------------------------------------

GET /follow-ups

Permission:

room_board.follow_up.view

--------------------------------------------------

POST /follow-ups

Permission:

room_board.follow_up.create

--------------------------------------------------

POST /follow-ups/{follow_up_id}/resolve

Permission:

room_board.follow_up.resolve

--------------------------------------------------

GET /service-month-matrix

Permission:

room_board.biller.view

--------------------------------------------------

GET /activity

Permission:

room_board.audit.view_limited

ACCEPTANCE

□ Every endpoint is assignment scoped.

□ Unassigned agencies cannot be queried.

□ Claim submission requires explicit permission.

□ Payment allocation requires explicit permission.

□ All mutation endpoints are audited.

□ Idempotency keys protect import and submission endpoints.

□ API errors do not reveal unauthorized record existence.

--------------------------------------------------

GITHUB ISSUE 7.2

TITLE

[Biller Platform] Implement Room & Board Billing & Reimbursement Center UI

REQUIRED SECTIONS

- Executive Room & Board Reimbursement Exposure
- Monthly Billing Queue
- Payer Reimbursement Queue
- Payment Allocation
- Payer Follow-Up Queue
- Service-Month Reimbursement Matrix
- Hospice-Funded Pass-Through Advance Tracker
- System Audit and Transaction Log

ACCEPTANCE

□ Current assigned agency is visible.

□ Training environment is clearly labeled.

□ Exact payer amount is visible.

□ Exact payer payment date is visible.

□ Service month is visible.

□ Short and partial payments are visible.

□ Allocation status is visible.

□ Follow-up queue is actionable.

□ Advance status is visible.

□ UI matches approved Figma.

==================================================
MILESTONE 8
TENANT PLATFORM API AND UI
==================================================

GITHUB ISSUE 8.1

TITLE

[Tenant Platform] Implement Room & Board Financial Reconciliation APIs

LOGICAL ROUTE NAMESPACE

/api/tenant/room-board

Use existing API-version conventions.

ENDPOINTS

GET /summary

Purpose:

Return current agency financial summary.

Permission:

room_board.tenant.view

--------------------------------------------------

GET /advances

Purpose:

Return hospice-funded advances.

Permission:

room_board.advance.view

--------------------------------------------------

GET /snf-payables

Permission:

room_board.snf_payable.view

--------------------------------------------------

GET /snf-payables/{payable_id}

Permission:

room_board.snf_payable.view

--------------------------------------------------

POST /snf-payables

Permission:

room_board.snf_payable.create

--------------------------------------------------

POST /snf-payables/{payable_id}/approve

Permission:

room_board.snf_payable.approve

--------------------------------------------------

POST /snf-payables/{payable_id}/hold

Permission:

room_board.snf_payable.hold

--------------------------------------------------

POST /snf-payables/{payable_id}/adjustments

Permission:

room_board.snf_adjustment.propose

--------------------------------------------------

POST /snf-payables/{payable_id}/payments

Purpose:

Record an authoritative SNF payment.

Permission:

room_board.snf_payment.record

--------------------------------------------------

POST /snf-payments/{payment_id}/void

Permission:

room_board.snf_payment.void

--------------------------------------------------

POST /snf-payments/{payment_id}/reissue

Permission:

room_board.snf_payment.reissue

--------------------------------------------------

GET /reimbursement-aging

Permission:

room_board.tenant.view

--------------------------------------------------

GET /snf-liability-aging

Permission:

room_board.tenant.view

--------------------------------------------------

GET /service-month-ledger

Permission:

room_board.tenant.view

--------------------------------------------------

POST /service-periods/{period_id}/reconcile

Permission:

room_board.reconciliation.perform

--------------------------------------------------

POST /reconciliations/{reconciliation_id}/reopen

Permission:

room_board.reconciliation.reopen

--------------------------------------------------

GET /annual-support-schedule

Permission:

room_board.reporting.view

--------------------------------------------------

POST /annual-support-schedule/export

Permission:

room_board.reporting.export

ACCEPTANCE

□ APIs are restricted to the authenticated tenant agency.

□ Tenant users cannot access other agencies.

□ SNF payment recording requires authoritative evidence.

□ Payable approval is separated from payment recording when configured.

□ Annual export is audited.

□ Export is labeled as a supporting schedule, not an official completed cost report.

--------------------------------------------------

GITHUB ISSUE 8.2

TITLE

[Tenant Platform] Implement Room & Board Financial Reconciliation Center UI

REQUIRED SECTIONS

- Executive Room & Board Reimbursement Exposure
- Hospice-Funded Pass-Through Advances
- Facility SNF Pass-Through Disbursements
- Payer Reimbursement Aging
- Facility Liability Aging
- Service-Month Reconciliation Ledger
- Annual Cost Reporting Summary

ACCEPTANCE

□ Medi-Cal reimbursement received is visible.

□ HMO reimbursement received is visible.

□ Awaiting Medi-Cal is visible.

□ Awaiting HMO is visible.

□ Exact reimbursement date is visible.

□ Exact SNF payment date is visible.

□ Outstanding reimbursement is visible.

□ SNF payable is visible.

□ Hospice-funded advance is visible.

□ Service-month status is visible.

□ Annual support export is available to authorized roles.

□ UI matches approved Figma.

==================================================
MILESTONE 9
ROLE-BASED ACCESS CONTROL
==================================================

GITHUB ISSUE 9.1

TITLE

[Security] Implement Room & Board role and permission matrix

IMPORTANT

Map these logical roles to existing repository roles.

Do not create duplicate roles if equivalent authority already exists.

--------------------------------------------------
BILLER STAFF
--------------------------------------------------

May:

- View assigned Room & Board cases
- View assigned claims
- Prepare billing periods
- Run validation
- Prepare claims
- Record payer follow-up
- View remittances
- Propose payment allocations
- View limited activity history

May not:

- View unassigned agencies
- Approve SNF payables
- Record SNF payments unless separately authorized
- Export tenant annual financial schedules
- Modify tenant financial configuration
- Submit claims unless claim-submit permission is granted

--------------------------------------------------
BILLER CLAIM SUBMITTER
--------------------------------------------------

May perform Biller Staff actions plus:

- Submit claims
- Correct and resubmit claims
- Record external claim responses

--------------------------------------------------
BILLER PAYMENT POSTER
--------------------------------------------------

May:

- Import or record remittances
- Allocate payer payments
- Correct allocations
- Reverse allocations with reason and authority
- Mark reimbursement review complete

May not:

- Approve SNF payables
- Issue SNF payments

--------------------------------------------------
BILLING MANAGER
--------------------------------------------------

May:

- View all Room & Board work for assigned agencies
- Reassign billing work
- Approve configured billing actions
- Review disputes
- Review allocation corrections
- View expanded audit history
- Export operational billing reports

--------------------------------------------------
TENANT OFFICE MANAGER
--------------------------------------------------

May:

- View current agency summary
- View payer reimbursement dates and amounts
- View SNF payables
- View SNF payments
- View advances
- View reconciliation
- Export authorized agency reports
- Record supporting evidence where permitted

May not:

- Access another agency
- Submit payer claims by default
- Approve SNF payments without separate authority

--------------------------------------------------
TENANT FINANCE STAFF
--------------------------------------------------

May:

- Create SNF payable drafts
- Record invoices
- Propose adjustments
- Record SNF payments when authorized
- Perform reconciliation
- Produce support schedules

--------------------------------------------------
TENANT FINANCIAL APPROVER
--------------------------------------------------

May:

- Approve SNF payables
- Approve adjustments
- Approve voids and reissues
- Close financial periods
- Reopen reconciliation with reason
- Export annual reporting support

--------------------------------------------------
TENANT ADMINISTRATOR
--------------------------------------------------

May:

- View all Room & Board records for the tenant
- Assign agency financial work
- Manage agency-specific workflow configuration
- View audit history

May not receive platform-wide access.

--------------------------------------------------
READ-ONLY AUDITOR
--------------------------------------------------

May:

- View authorized historical records
- View evidence
- View audit history
- Export specifically authorized audit packages

May not mutate financial records.

--------------------------------------------------
SNS PLATFORM SUPPORT
--------------------------------------------------

May access only through approved, attributable support workflow.

Platform authority does not automatically establish routine operational access to patient and financial data.

SUPPORT ACCESS MUST BE:

- Authorized
- Time bounded where supported
- Audited
- Minimum necessary
- Reason coded

RBAC ACCEPTANCE

□ Permissions are server enforced.

□ UI actions reflect effective permissions.

□ Hidden UI is not the only security control.

□ Biller assignment is enforced.

□ Tenant boundary is enforced.

□ Mutation authority is action specific.

□ Read-only users cannot mutate records.

□ Authorization failure replaces the protected workspace.

□ No protected values remain rendered after denial.

==================================================
MILESTONE 10
PROPOSED DATABASE SCHEMA
==================================================

GITHUB ISSUE 10.1

TITLE

[Database] Implement verified Room & Board schema using forward-only migrations

IMPORTANT

The following table names are proposed logical names.

Final physical names must follow repository conventions after discovery.

Do not create duplicates.

--------------------------------------------------
room_board_cases
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- patient_id UUID not null
- facility_id UUID not null
- payer_id UUID not null
- coverage_id UUID nullable
- agreement_id UUID nullable
- election_date date not null
- eligibility_start_date date nullable
- eligibility_end_date date nullable
- case_status varchar or approved enum not null
- applicability_status varchar not null
- rate_source_id UUID nullable
- assigned_biller_id UUID nullable
- created_by UUID not null
- updated_by UUID not null
- created_at timestamptz not null
- updated_at timestamptz not null
- closed_at timestamptz nullable
- version integer not null default 1
- supersedes_case_id UUID nullable

Relationships:

- tenant
- agency
- patient
- facility
- payer
- coverage
- agreement
- assigned biller
- service periods
- claims
- events
- evidence

Constraints:

- patient tenant must match case tenant
- agency must belong to tenant
- eligibility_end_date cannot precede eligibility_start_date
- supersedes_case_id cannot reference itself
- closed_at required when case status is Closed
- no physical delete after financial activity exists

Indexes:

- tenant_id, agency_id, case_status
- tenant_id, patient_id
- tenant_id, facility_id
- tenant_id, payer_id
- assigned_biller_id, case_status
- election_date
- eligibility_end_date

Partial uniqueness:

Prevent duplicate active cases for the same:

tenant + patient + facility + payer + overlapping eligibility period

Use the safest repository-supported constraint strategy.

--------------------------------------------------
room_board_service_periods
--------------------------------------------------

Columns:

- id UUID primary key
- room_board_case_id UUID not null
- tenant_id UUID not null
- agency_id UUID not null
- patient_id UUID not null
- facility_id UUID not null
- payer_id UUID not null
- service_from date not null
- service_through date not null
- service_month date not null
- eligible_days integer not null
- expected_reimbursement numeric(14,2) not null
- expected_snf_obligation numeric(14,2) not null
- share_of_cost numeric(14,2) not null default 0
- claimed_amount numeric(14,2) not null default 0
- reimbursement_status varchar not null
- snf_payable_status varchar not null
- reconciliation_status varchar not null
- advance_status varchar not null
- rate_source_id UUID nullable
- calculation_version varchar not null
- created_at timestamptz not null
- updated_at timestamptz not null
- version integer not null default 1
- supersedes_period_id UUID nullable

Constraints:

- service_through >= service_from
- eligible_days >= 0
- monetary amounts >= 0 unless an approved correction record permits signed values
- tenant and patient scope must match
- service month normalized to approved month boundary
- supersedes_period_id cannot reference itself

Indexes:

- tenant_id, agency_id, service_month
- room_board_case_id, service_month
- patient_id, service_month
- facility_id, service_month
- payer_id, reimbursement_status
- reconciliation_status
- advance_status

Unique active period:

- room_board_case_id + service_from + service_through + active-version indicator

--------------------------------------------------
room_board_claims
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- service_period_id UUID not null
- payer_id UUID not null
- claim_number varchar nullable
- submission_sequence integer not null
- claim_status varchar not null
- amount_billed numeric(14,2) not null
- validation_result_id UUID nullable
- submitted_at timestamptz nullable
- submitted_by UUID nullable
- payer_received_at timestamptz nullable
- processed_at timestamptz nullable
- external_reference varchar nullable
- correction_reason text nullable
- supersedes_claim_id UUID nullable
- created_at timestamptz not null
- updated_at timestamptz not null
- version integer not null default 1

Constraints:

- amount_billed >= 0
- submission_sequence > 0
- submitted_at required for Submitted and downstream states
- supersedes_claim_id cannot reference itself
- tenant and service-period scope must match

Indexes:

- tenant_id, agency_id, claim_status
- service_period_id, submission_sequence
- payer_id, claim_status
- claim_number
- external_reference
- submitted_at

Unique:

- service_period_id + submission_sequence

--------------------------------------------------
room_board_claim_events
--------------------------------------------------

Columns:

- id UUID primary key
- claim_id UUID not null
- tenant_id UUID not null
- event_type varchar not null
- previous_status varchar nullable
- new_status varchar not null
- actor_id UUID nullable
- actor_type varchar not null
- reason text nullable
- source_reference varchar nullable
- occurred_at timestamptz not null
- correlation_id UUID not null
- created_at timestamptz not null

Append-only.

Indexes:

- claim_id, occurred_at
- tenant_id, occurred_at
- event_type, occurred_at
- correlation_id

--------------------------------------------------
room_board_remittances
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- payer_id UUID not null
- payment_reference varchar not null
- payment_amount numeric(14,2) not null
- payment_date date not null
- received_date date nullable
- check_number varchar nullable
- eft_trace varchar nullable
- remittance_reference varchar nullable
- source_type varchar not null
- source_document_id UUID nullable
- remittance_status varchar not null
- reversal_of_remittance_id UUID nullable
- created_by UUID nullable
- created_at timestamptz not null

Constraints:

- payment_amount >= 0
- reversal record references original
- reversal cannot reference itself
- tenant and payer scope must be consistent

Indexes:

- tenant_id, agency_id, payment_date
- payer_id, payment_date
- payment_reference
- eft_trace
- check_number
- remittance_status

Idempotency uniqueness:

Use a verified composite such as:

tenant + payer + payment reference + payment date + amount

Do not rely on a weak identity if payer references can repeat.

--------------------------------------------------
room_board_payment_allocations
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- remittance_id UUID not null
- service_period_id UUID not null
- claim_id UUID nullable
- patient_id UUID not null
- facility_id UUID not null
- allocated_amount numeric(14,2) not null
- adjustment_amount numeric(14,2) not null default 0
- allocation_status varchar not null
- allocated_by UUID not null
- allocated_at timestamptz not null
- correction_of_allocation_id UUID nullable
- reversal_of_allocation_id UUID nullable
- evidence_reference_id UUID nullable
- created_at timestamptz not null

Constraints:

- allocated_amount >= 0
- correction and reversal references cannot point to self
- remittance, service period, patient, facility, and claim must share tenant scope
- active allocated total cannot exceed remittance availability under approved rules

Indexes:

- remittance_id, allocation_status
- service_period_id
- claim_id
- patient_id
- facility_id
- tenant_id, allocated_at

--------------------------------------------------
room_board_snf_payables
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- service_period_id UUID not null
- facility_id UUID not null
- patient_id UUID not null
- invoice_number varchar nullable
- invoice_date date nullable
- due_date date nullable
- invoice_amount numeric(14,2) not null
- approved_amount numeric(14,2) nullable
- share_of_cost numeric(14,2) not null default 0
- adjustment_amount numeric(14,2) not null default 0
- remaining_payable numeric(14,2) not null
- payable_status varchar not null
- approved_by UUID nullable
- approved_at timestamptz nullable
- agreement_id UUID nullable
- created_by UUID not null
- created_at timestamptz not null
- updated_at timestamptz not null
- version integer not null default 1
- supersedes_payable_id UUID nullable

Constraints:

- invoice_amount >= 0
- approved_amount >= 0 when populated
- share_of_cost >= 0
- due_date cannot precede invoice_date unless documented exception exists
- approved_by and approved_at required for approved states
- tenant, agency, patient, facility, and period scope must match
- supersedes_payable_id cannot reference itself

Indexes:

- tenant_id, agency_id, payable_status
- service_period_id
- facility_id, payable_status
- patient_id
- due_date
- invoice_number

--------------------------------------------------
room_board_snf_payments
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- snf_payable_id UUID not null
- facility_id UUID not null
- patient_id UUID not null
- service_period_id UUID not null
- payment_amount numeric(14,2) not null
- payment_date date not null
- payment_method varchar not null
- check_number varchar nullable
- eft_reference varchar nullable
- payment_status varchar not null
- approved_by UUID nullable
- recorded_by UUID not null
- evidence_document_id UUID nullable
- voids_payment_id UUID nullable
- reissues_payment_id UUID nullable
- created_at timestamptz not null

Constraints:

- payment_amount >= 0
- void and reissue references cannot point to self
- payable, facility, patient, and service period must share scope
- payment requires approved payable unless approved override is recorded

Indexes:

- tenant_id, agency_id, payment_date
- snf_payable_id
- facility_id, payment_date
- patient_id
- service_period_id
- check_number
- eft_reference
- payment_status

--------------------------------------------------
room_board_reconciliations
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- service_period_id UUID not null
- expected_reimbursement numeric(14,2) not null
- claimed_amount numeric(14,2) not null
- allocated_reimbursement numeric(14,2) not null
- payer_adjustments numeric(14,2) not null default 0
- snf_obligation numeric(14,2) not null
- snf_paid numeric(14,2) not null
- facility_adjustments numeric(14,2) not null default 0
- outstanding_reimbursement numeric(14,2) not null
- outstanding_snf_payable numeric(14,2) not null
- hospice_funded_advance numeric(14,2) not null
- reconciliation_status varchar not null
- calculation_version varchar not null
- reconciled_by UUID nullable
- reconciled_at timestamptz nullable
- closed_by UUID nullable
- closed_at timestamptz nullable
- reopened_by UUID nullable
- reopened_at timestamptz nullable
- reopen_reason text nullable
- snapshot_data jsonb not null
- supersedes_reconciliation_id UUID nullable
- created_at timestamptz not null

Constraints:

- supersedes reference cannot point to self
- reconciled actor and date required for reconciled states
- closed actor and date required for Closed
- reopen reason required for reopened state
- tenant and service-period scope must match

Indexes:

- tenant_id, agency_id, reconciliation_status
- service_period_id, created_at
- outstanding_reimbursement
- hospice_funded_advance
- reconciled_at
- closed_at

--------------------------------------------------
room_board_follow_ups
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- agency_id UUID not null
- service_period_id UUID not null
- claim_id UUID nullable
- payer_id UUID not null
- assigned_user_id UUID nullable
- follow_up_status varchar not null
- action_type varchar not null
- last_contact_date date nullable
- next_action_date date nullable
- contact_method varchar nullable
- payer_reference varchar nullable
- contact_note text nullable
- resolution_note text nullable
- resolved_at timestamptz nullable
- created_at timestamptz not null
- updated_at timestamptz not null

Constraints:

- next action may not precede last contact unless reason is documented
- resolved date required for resolved status
- tenant scope must match source records

Indexes:

- tenant_id, agency_id, follow_up_status
- assigned_user_id, follow_up_status
- payer_id, follow_up_status
- next_action_date
- service_period_id

Prevent duplicate active follow-up for the same service period, payer, and action type.

--------------------------------------------------
room_board_evidence_references
--------------------------------------------------

Columns:

- id UUID primary key
- tenant_id UUID not null
- entity_type varchar not null
- entity_id UUID not null
- document_id UUID nullable
- source_record_type varchar nullable
- source_record_id UUID nullable
- page_number integer nullable
- source_location varchar nullable
- evidence_type varchar not null
- captured_by UUID nullable
- captured_at timestamptz not null
- created_at timestamptz not null

Indexes:

- tenant_id, entity_type, entity_id
- document_id
- source_record_type, source_record_id

--------------------------------------------------
room_board_audit_events
--------------------------------------------------

Use existing shared audit-event model if authoritative.

If extension is required, ensure support for:

- tenant_id
- agency_id
- actor_id
- actor_role
- platform_context
- action
- entity_type
- entity_id
- patient_id
- facility_id
- payer_id
- service_period_id
- previous_state
- new_state
- exact_amount_before
- exact_amount_after
- reason
- correlation_id
- occurred_at
- ruleset_version
- metadata

Indexes:

- tenant_id, occurred_at
- agency_id, occurred_at
- actor_id, occurred_at
- entity_type, entity_id, occurred_at
- patient_id, occurred_at
- facility_id, occurred_at
- correlation_id

Audit events are append-only.

==================================================
MILESTONE 11
REPORTING AND EXPORTS
==================================================

GITHUB ISSUE 11.1

TITLE

[Tenant Platform] Implement annual Room & Board reconciliation support schedule

REQUIRED EXPORT FIELDS

- Fiscal Year
- Agency
- Patient
- Facility
- Payer
- Service Period
- Eligible Days
- Expected Reimbursement
- Amount Billed
- Amount Received
- Exact Reimbursement Date
- Payer Payment Reference
- Amount Due to SNF
- Amount Paid to SNF
- Exact SNF Payment Date
- Outstanding Reimbursement
- Outstanding SNF Payable
- Hospice-Funded Advance
- Adjustments
- Dispute Status
- Reconciliation Status
- Evidence References

REQUIRED LABEL

Room & Board Financial Reconciliation Support Schedule

Do not label:

Official Medicare Cost Report

ACCEPTANCE

□ Report is fiscal-year scoped.

□ Report is tenant scoped.

□ Report includes exact payer dates.

□ Report includes exact SNF dates.

□ Report reconciles to shared source records.

□ Export activity is audited.

□ No unauthorized agency data is included.

==================================================
MILESTONE 12
AUDIT, SECURITY, AND CROSS-PLATFORM CONSISTENCY
==================================================

GITHUB ISSUE 12.1

TITLE

[Security] Verify Room & Board cross-platform isolation

TESTS

□ Biller cannot view an unassigned agency.

□ Biller cannot access Tenant financial actions without permission.

□ Tenant user cannot submit claims through Biller APIs.

□ Tenant user cannot access another tenant.

□ (Document truncated in source at this point — see Note below.)

==================================================
NOTE ON SOURCE COMPLETENESS
==================================================

The dictated source content for this document ends mid-list inside
Milestone 12 / GitHub Issue 12.1 ("Verify Room & Board cross-platform
isolation"). The remaining acceptance tests for Milestone 12 (and any
further milestones, e.g. test/QA requirements, migration rollout plan,
or a final locked-status block) were not included in the source paste
and are marked here as **pending continuation** rather than invented.
This document should be updated in place when the remainder is
provided, rather than creating a new file.

==================================================
RELATIONSHIP TO OTHER DOCUMENTS
==================================================

This document is the detailed engineering-level implementation plan
(Epic, Milestones 0-12, GitHub Issues, API routes, permission matrix,
and full field-level database schema) for the Room & Board domain
introduced at the product/spec level as **Page 11** in
`docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`
("Room & Board Billing & Reimbursement Center" / "Room & Board
Financial Reconciliation Center"). That document remains the
authoritative product/UX specification (KPI cards, required sections,
statuses, AI governance, acceptance criteria, Epic Summary, and a
7-milestone summary); this document is the corresponding technical
build plan and supersedes any earlier Facility Collections / Contract
Recovery implementation brief for this workflow — the former Facility
Collections / Contract Recovery data model must not be implemented.

Per the Verify-First Requirement above, no schema, migration, API,
service, or UI work may begin until repository discovery
(Milestone 0 / GitHub Issue 0.1, deliverable
`docs/room-board/ROOM_BOARD_DISCOVERY_REPORT.md`) is complete and
reviewed. That discovery report has not yet been created.

## Change Log

| Date | Change |
|---|---|
| 2026-09-17 | Document created — Room & Board Implementation Plan, Schema, and Issues. Full engineering-level Epic (14-item acceptance list), Milestone 0 (Repository Discovery and Model Mapping, blocking all further work), Milestone 1 (Shared Room & Board Domain Foundation — RoomBoardCase, RoomBoardServicePeriod), Milestone 2 (Room & Board Billing and Claim Lifecycle — validation and a 17-state submission lifecycle), Milestone 3 (Payer Remittance and Payment Allocation — a 7-state allocation lifecycle supporting one-remittance-to-many allocations), Milestone 4 (SNF Payables and SNF Payments — 13-state payable lifecycle, 9-state payment lifecycle), Milestone 5 (Hospice-Funded Advance Engine — 7-state advance lifecycle with an explicit non-double-counting calculation rule), Milestone 6 (Reconciliation Engine — a 15-state reconciliation lifecycle with independent status tracking across claim/payer/SNF/reconciliation), Milestone 7 (Biller Platform API and UI — full REST endpoint list under `/api/biller/room-board` plus required UI sections), Milestone 8 (Tenant Platform API and UI — full REST endpoint list under `/api/tenant/room-board` plus required UI sections), Milestone 9 (Role-Based Access Control — a 9-role permission matrix: Biller Staff, Biller Claim Submitter, Biller Payment Poster, Billing Manager, Tenant Office Manager, Tenant Finance Staff, Tenant Financial Approver, Tenant Administrator, Read-Only Auditor, SNS Platform Support), Milestone 10 (Proposed Database Schema — full column/constraint/index specifications for `room_board_cases`, `room_board_service_periods`, `room_board_claims`, `room_board_claim_events`, `room_board_remittances`, `room_board_payment_allocations`, `room_board_snf_payables`, `room_board_snf_payments`, `room_board_reconciliations`, `room_board_follow_ups`, `room_board_evidence_references`, and `room_board_audit_events`), Milestone 11 (Reporting and Exports — annual Room & Board Financial Reconciliation Support Schedule, explicitly not an Official Medicare Cost Report), and the start of Milestone 12 (Audit, Security, and Cross-Platform Consistency — cross-platform isolation tests). The source paste ends mid-list within Milestone 12 / GitHub Issue 12.1; the remainder is pending continuation and is not invented here. Documentation only; no schema, migrations, tables, or models created. This document explicitly supersedes the earlier Facility Collections / Contract Recovery implementation brief for this workflow, which must not be implemented. |
