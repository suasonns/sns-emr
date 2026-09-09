# Eligibility Integrity Review (Phase 10)

Status: verification only. No production code changed. No billing feature or AI built.
Evidence basis: direct file/line reads of `app/services/benefit_period_service.py`,
`app/api/benefits.py`, `app/models/certification.py`, `app/services/certification_service.py`,
`app/services/dashboard_service.py`, `app/billing/services/billing_readiness_service.py`,
`app/api/patients.py`. No claim in this document is inferred from an endpoint or table merely existing.

---

## Q1 — Can a patient enter a new benefit period without finalized certification?

**YES.**

- **Service** (`app/services/benefit_period_service.py:38-172`, `rollover_benefit_period`): validates
  `benefit_type in {"INITIAL","RECERT"}`, row-locks existing `BenefitPeriod` rows, checks idempotency
  (exact `start_date`+`benefit_type`+`tenant_id`+`patient_id` match), validates chronology
  (`start_date` not before current BP's `start_date`), computes CMS period length/number, closes the
  old current BP, creates the new BP, seeds an `IDG_REVIEW` task, commits. **No query against the
  `certifications` table appears anywhere in this function.**
- **API** (`app/api/benefits.py:60`, `POST /benefits/`): role-gates to RN/Administrator, passes the
  request body straight to `rollover_benefit_period`. No certification lookup, no certification
  status check, no `benefit_period_id`-to-`certification` join.
- **Database**: `benefit_periods` table has no FK to `certifications` and no trigger/constraint
  enforcing a certification must exist. The FK relationship runs the other direction —
  `certifications.benefit_period_id` (`app/models/certification.py:34`) is `nullable=False`, i.e. a
  **Certification requires an existing BenefitPeriod**, not the reverse. This means the only
  structurally possible sequence today is BenefitPeriod-first, Certification-second — the opposite of
  the CMS-correct order (certification should gate the period it covers).
- **UI**: no frontend caller for `POST /benefits/` was found anywhere in `sns-emr-frontend/src`
  (confirmed in the prior `benefit_period_engine_review.md` search) — the only currently-known caller
  is direct API invocation or the guardrail test suite. This narrows real-world exposure today but
  does not change the code-path finding.

## Q2 — Can `rollover_benefit_period` execute when...

| Condition | Result | Evidence |
|---|---|---|
| Certification Missing | **YES** | No certification query in the function at all. |
| Certification Expired | **YES** | `expires_at` on `Certification` is never read by this function. |
| Certification Draft | **YES** | `Certification.status` (`DRAFT`/`PENDING_SIGNATURE`/`FINALIZED`/`SUPERSEDED`) is never read by this function. |
| Recert Missing | **YES** | `benefit_type="RECERT"` is accepted as a bare string literal with no cross-check that any `Certification(cert_type="RECERT")` row exists for the patient. |

## Q3 — What SHOULD happen (intended behavior, not current behavior)

CMS hospice election-period rule (42 CFR §418.21/§418.22) requires a **valid, timely certification or
recertification signed by the required physician(s) before the corresponding benefit period is
billable**. The intended sequence:

```
Initial Certification (signed, FINALIZED, cert_type=INITIAL)
        ↓ gates
Benefit Period 1 (90 days)
        ↓ approaching day ~75-90, Recertification must be signed
Recertification (signed, FINALIZED, cert_type=RECERT)
        ↓ gates
Benefit Period 2 (90 days)
        ↓ approaching end, Recertification must be signed again
Recertification (signed, FINALIZED, cert_type=RECERT)
        ↓ gates
Benefit Period 3+ (60 days each, recurring)
```

Required rules the system should enforce but currently does not:
1. `rollover_benefit_period(benefit_type="INITIAL")` should require a `Certification` row with
   `cert_type="INITIAL"`, `status="FINALIZED"`, `signed_at IS NOT NULL` for the patient before creating BP1.
2. `rollover_benefit_period(benefit_type="RECERT")` should require a `Certification` row with
   `cert_type="RECERT"`, `status="FINALIZED"`, `signed_at IS NOT NULL`, and `effective_date` consistent
   with the new period's `start_date`, before creating BP2+.
3. A certification with `expires_at` in the past should not be treated as satisfying the gate for a
   *new* period (an expired cert is a valid historical record but does not authorize forward advancement).
4. The gate should be enforced at the point of creation (service layer), not only re-derived later at
   billing-readiness time — defense-in-depth, not a single late checkpoint.

## Q4 — Bypass surfaces

| Caller | Can bypass certification? | Evidence |
|---|---|---|
| API callers | **YES** | Same `rollover_benefit_period` code path as everyone else; no certification check exists for any caller to hit. |
| Administrators | **YES** | `benefits.py` role-gate is `{RN, Administrator}` — Administrator is explicitly permitted, and the function contains no additional business-rule gate for any role. |
| Background jobs | **N/A / not evaluated as a real bypass** — no scheduled job or cron task calling `rollover_benefit_period` was found in this codebase (grep for all call sites returned only `benefits.py` and test files). This is not a bypass surface today because it doesn't exist, but it also means there is no automatic recert-driven rollover safety net either. |

## Q5 — What enforcement currently exists (by category)

- **Technical enforcement**: row locking (`with_for_update`), idempotency check on exact duplicate
  requests, chronology validation (`start_date` vs. current BP `start_date`), atomic
  commit/rollback. All present and correct (confirmed by 4/4 passing guardrail tests, prior segment).
- **Business-rule enforcement**: **none** at benefit-period creation time. `benefit_type` is checked
  only against a 2-value literal set — it is never checked against any actual clinical record.
- **Audit enforcement**: **none**. `BenefitPeriod.created_by` is never populated; no
  `append_audit_event`/`build_audit_event` call exists anywhere in `benefit_period_service.py`. Contrast:
  `Certification` status transitions ARE audited via a dedicated, real, append-only
  `CertificationStatusEvent` table (`app/models/certification.py:77-104`, populated by
  `app/services/certification_service.py`) — the audit-trail gap is specific to `BenefitPeriod`, not
  organization-wide as previously stated; it is narrower and more fixable than earlier documents implied.
- **User-visible enforcement**: **none** at creation time. However, downstream at billing-readiness
  time, `_has_finalized_certification()` (`app/billing/services/billing_readiness_service.py:129-152`)
  does re-check `status='FINALIZED' AND signed_at IS NOT NULL` for the specific `benefit_period_id`
  being billed, and surfaces a human-readable blocker reason ("Certification of Terminal Illness
  (CTI/Recert) is not signed..."). This is a real, working safety net — just a *late* one, after the
  BenefitPeriod (and any downstream records referencing it) may already exist.

## Q6 — Can SNS currently answer "Why is this patient eligible?"

**Partially / conditionally YES, but only at the billing-readiness layer, not at the benefit-period
layer.**

- `check_patient_billing_readiness()` (`billing_readiness_service.py:216+`) independently re-derives
  eligibility from real data at call time: finalized certification for the specific benefit period,
  attested F2F, physician-approved POC, NOE timeliness/exception reason, payer sequence. If all checks
  pass, the absence of blockers **is** the eligibility answer, and it is traceable to real source data
  (not inferred from BenefitPeriod existence).
- What SNS **cannot** currently answer: "why does this BenefitPeriod exist at all" — there is no
  equivalent check gating BenefitPeriod *creation*, so a BenefitPeriod's mere existence carries no
  eligibility guarantee. The two questions ("is this BP billable" vs. "should this BP exist") are
  answered by two different layers today, and only one of them has a gate.

## Q7 — Can SNS currently answer "Why is this patient NOT eligible?"

**YES, at the billing-readiness layer.** `check_patient_billing_readiness()` returns a `blockers` list
of short, human-readable reason strings (e.g. "Certification of Terminal Illness is not signed",
"Payer sequence is ambiguous: ...", NOE timeliness reasons) — this is a real, working "why not"
explainer, already built, already wired to real data. It is not fabricated (unlike the 835 remittance
widget documented in the Phase 5/6 review). The gap is that this "why not" logic runs only when
billing is attempted — it does not run, and cannot block, at benefit-period creation time.

---

## Direct Answer — Most Important Question

**Can SNS currently create an ACTIVE BILLABLE BENEFIT PERIOD without finalized certification?**

**YES.**

A `BenefitPeriod` with `is_current=True` can be created via `POST /benefits/` (RN or Administrator)
with zero certification of any kind on file for the patient. It will **not**, however, pass
`check_patient_billing_readiness()` — if a claim is attempted against it, the missing-certification
blocker will fire and surface a specific reason. So: the *period* can be created and will sit as
"current" with no certification; a *bill* against it will currently be correctly blocked by the
readiness engine. The eligibility integrity failure is at the period-creation layer, not (today) at
the claim-blocking layer.
