# Claim State Machine

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Formal state machine specification requested before any new billing
functionality is added, given the confirmed backward-transition defect.
This document formalizes what already exists (per
`claim_status_architecture.md`, restated here in the requested
state-machine format) and specifies what governance would need to be
added — it does not itself implement anything.

## States

`READY`, `SENT`, `ACCEPTED`, `PAID`, `DENIED` — five states, confirmed
authoritative (no `GENERATED` state exists in the real code).

## Per-state transition table

| State | Allowed Transitions (as designed, `ALLOWED_TRANSITIONS`) | Disallowed Transitions | Writers | Readers | Audit Requirement | Override Workflow |
|---|---|---|---|---|---|---|
| `READY` | → `SENT` | → `ACCEPTED`, `PAID`, `DENIED` (no direct jump) | `update_claim_status` (enforced) | `list_claims` (`GET /billing/claims`) | `CLAIM_STATUS_CHANGED` audit event — **enforced today** | None needed (forward-only, uncontroversial) |
| `SENT` | → `ACCEPTED`, `DENIED` | → `PAID` directly (must pass through `ACCEPTED` per the enforced rule) | `update_claim_status` (enforced); **also** `export_patient_claim_edi` writes `SENT` **from any state**, and `post_payments_from_835` writes `ACCEPTED`/`DENIED`-adjacent outcomes when matched | Same | Enforced only for the primary writer; **NOT enforced or audited** for the other two (confirmed gap) | None exists |
| `ACCEPTED` | → `PAID`, `DENIED` | → `SENT`, `READY` | `update_claim_status` (enforced); `post_payments_from_835` (own independent guard, confirmed correct by execution) | Same | Enforced + audited for primary writer only | None exists |
| `PAID` | **(none — terminal by design)** | → anything | *Should be none.* **Confirmed defect**: `export_patient_claim_edi` can still write `SENT` over a `PAID` claim, bypassing the empty allowed-set entirely, because it does not consult `ALLOWED_TRANSITIONS` at all | Same | **NO audit event for the writer that can violate this state's terminality** | **None exists** — this is precisely the gap this document is meant to close |
| `DENIED` | **(none — terminal by design)** | → anything | Same risk profile as `PAID` — `export_patient_claim_edi`'s bypass applies equally here | Same | Same gap | Same gap |

## Is PAID terminal?

**YES — by design, with documented evidence, restated from
`claim_status_architecture.md` §5:**

- `ALLOWED_TRANSITIONS["PAID"] = set()` in the primary, enforced writer
  — an explicit empty set, not an omission.
- `post_payments_from_835`, the one other writer with its own
  independent guard, was deliberately coded to only transition
  `SENT`/`ACCEPTED` claims — confirmed by execution that it leaves an
  already-`PAID`/`DENIED` claim untouched on a repeat posting.
- No correction/reopen/reversal workflow exists anywhere in the
  codebase (no matching endpoint, comment, docstring, or test).

**The one writer that violates this (`export_patient_claim_edi`) is a
confirmed defect, not an intentional exception.** This document
reaffirms that conclusion rather than re-deriving it, since it was
already proven by execution in Phase 4
(`test_export_patient_claim_edi_bypasses_allowed_transitions_for_real`).

## Required governance (specification, not yet implemented)

1. **Single enforcement point**: `export_patient_claim_edi` and
   `post_payments_from_835` should both route their `claim.status`
   writes through the same `ALLOWED_TRANSITIONS`-checking logic
   `update_claim_status` already uses, rather than each implementing
   (or, in one case, omitting) their own guard.
2. **Universal audit trail**: all three writers should call
   `append_audit_event`/`build_audit_event` with the same
   `CLAIM_STATUS_CHANGED` event shape `update_claim_status` already
   uses, so "show me every way a claim status changed" (the standing
   open question from `claim_status_architecture.md` §10) can finally be
   answered YES.
3. **Administrative correction workflow (new, does not exist today)**:
   if there is ever a legitimate business need to move a claim backward
   (e.g., a payment was posted in error), that must become an explicit,
   named, audited action — distinct from, and never accidentally
   triggered by, an export/re-export action. This document does not
   design that workflow's UX; it only states that one does not exist
   today and any backward movement must go through it once built, never
   through an unguarded side effect of an unrelated action.
4. **Override workflow**: none exists today for any terminal state; per
   item 3, one should be designed (separately) before any backward
   transition is ever intentionally allowed.

## Not built. This is the specification the "Claim Status Governance"
## priority would implement; nothing here has been changed in code.
