# RNICA Clinical Documentation Intelligence — Existing Infrastructure Map

**Status:** Requirements traceability against the "RNICA Clinical Documentation
Intelligence" directive (Voice-to-Documentation, Readiness Audit, Missing-Item
Navigation, Safe Finalization). No code, schema, or UI change made. Every
claim below is a verified file/line reference, not a memory recall.

**Governing rule applied:** reuse before create. This directive describes a
5-phase, ~22-section product architecture. Before any phase is scoped as
"build," this document establishes what already exists so Phase 1 work
extends real infrastructure instead of duplicating it.

**Headline finding:** a substantial majority of the directive's architecture
is **already built and in production use**, under different names, across
frontend and backend. This is not a greenfield build. The real work is
narrower than the directive reads on first pass: closing specific, named
gaps in an existing readiness/structured-findings/lock/audit system — not
constructing that system from nothing.

---

## 1. Directive → Existing System Map

| Directive concept (section) | RNICA equivalent | Status |
|---|---|---|
| "One documentation readiness service" (§3, §22.4) | `evaluate_finalization_readiness(form_data, poc_problems)` — `backend/app/services/clinical_note_validation_engine.py`, the **single shared function** called by both `GET /visits/rnica/{id}/finalization-readiness` (UI) and `POST /visits/rnica/{id}/lock` (server gate) | **Existing authoritative** |
| "Requirement registry" (§22.3) | `RN_ICA_REQUIRED_FIELD_GROUPS` (17-item hard-required field list, `clinical_note_validation_engine.py:380-517`) + `RNICA_LOCK_READINESS_MATRIX.md` (per-check applicability/enforcement/screen/lock-effect/audit-event table) | **Existing comparable** — has most but not all of the directive's exact columns (see §3 below) |
| "Blocking / Review Required / Improvement Suggested / Strength" classification (§6, §7) | Confirmed severity model: **Blocker / Warning / Informational / Conditional blocker** (`RNICA_LOCK_READINESS_MATRIX.md` §1) | **Existing comparable** — 4 tiers exist but do not line up 1:1; no "Strength" (positive-finding) tier exists today |
| "Direct Navigation to Missing Documentation" (§8) | Confirmed: `RNICACommandWorkspace.jsx` resolves a failed check to its owning module/route (`routeForRequirement`), performs `element.scrollIntoView({behavior:"smooth"})` and `.focus()` on the target field/narrative textarea | **Existing authoritative** — the mechanism described in the directive (open module → scroll → focus) is already implemented, not merely planned |
| "Finalization Rules" / blocking vs. non-blocking (§9) | Lock transaction (`visits.py`, `lock_rnica_assessment`): idempotent re-lock guard, `evaluate_finalization_readiness` call, `HTTPException(400, {unmetChecks, checks})` on failure, `RNICA_ASSESSMENT_LOCKED` audit event on success | **Existing authoritative** |
| "Readiness Status" states (§10: Not Started/In Progress/Review Required/Ready to Finalize/Finalized/Amended) | `record.status` (`DRAFT`/`LOCKED`) + `record.locked`/`locked_at` + amendment workflow (`correction-request`, `/amendments`, `/approve`/`/deny`) | **Existing comparable** — locked/amended states exist; "Review Required" as a distinct persisted status (vs. computed from unmet checks) is not confirmed to exist as its own stored value |
| "Voice-to-Documentation Workflow" (§4) | **Full pipeline already exists**: `POST /visit-recordings` (audio upload, consent-confirmed flag, idempotent via `client_recording_id`) → Azure Speech transcription (`transcript_status`: QUEUED/PROCESSING/COMPLETED/FAILED/RETRYING, with manual-entry FAILED-state fallback and staff-initiated retry) → `ai_note_draft: {narrative, section_notes, detected_topics, symptom_severity, structured_findings, generated_at, model}` | **Existing authoritative** — this is Phase 3 of the directive's own sequencing, already built |
| "Required Review Screen" before save (§4, §13) | `applyStructuredFindings.js` never auto-saves: every finding is either `appliedFields` (blank-only, immediately visible as a pending diff), `conflicts` (existing value differs — never overwritten), or `reviewNeeded` (non-CURRENT assertion status — never silently applied). `handleApplyStructuredSignal` in `RNICA.jsx` is a click-through, user-initiated action | **Existing authoritative** |
| "Structured Finding Provenance" (§12) | `CONCEPT_REGISTRY` (`structuredFindingRegistry.generated.js`, backend-generated via `scripts/generate_frontend_concept_registry.py`) + `structuredFieldProvenance` (`RNICA.jsx`, `handleApplyStructuredSignal`): captures `source_type`, `original_text_excerpt`, `recorded_at`, `confidence`, `signal.id` per applied field | **Existing authoritative** |
| "AI must not fill everything automatically" / prohibited outputs (§11) | `RNICA_AI_GOVERNANCE.md` — binding guardrail doc, already enumerates prohibited outputs (eligibility determination, prognosis generation, physician certification, auto-attestation/signature/lock/order/POC, new aggregate risk scores) and required/prohibited language lists | **Existing authoritative** — this is a governance document, not code, but it is binding and repository-validated (v2) |
| "Never overwrite a clinician-confirmed value" (§3C, §11) | `isBlank()`-gated writes in `applyStructuredFindings.js`; boolean-presence fields are explicitly **never** blank-eligible (a deliberate carve-out documented in-code) — always route to `conflicts` for RN confirmation | **Existing authoritative** |
| "Amendment workflow" / audit trail (§12, §16) | `POST /visits/rnica/{id}/correction-request`, `GET /visits/rnica/{id}/amendments`, `.../approve`, `.../deny` — distinct, timestamped, attributable; never mutates signed content. Backed by `rnica_amendment.py`/`rnica_amendment_service.py`, tested in `test_rnica_amendments.py` | **Existing authoritative** |
| "HOPE Validation... separate from clinical suggestions" (§16) | Confirmed conceptual separation exists (LCD `evaluateLCD` is explicitly "non-verdict shaped," per `RNICA_AI_GOVERNANCE.md` §3) but a formal `Official HOPE Fatal Edit` / `Official HOPE Warning Edit` label pairing (as literal UI-facing strings) was **not confirmed** this pass | **Existing comparable / partially unconfirmed** |
| Test coverage backbone (§20) | 16 backend test files directly exercise RNICA readiness/lock/amendment/structured-findings behavior (`test_rnica_finalization.py`, `test_structured_findings*.py` ×5, `test_rnica_amendments.py`, `test_evidence_harvester.py`, etc.) + `applyStructuredFindings.test.js` frontend | **Existing, substantial** |

## 2. What Phase 1-2 Already Has (do not rebuild)

Per the directive's own §21 sequencing ("do not attempt to build the entire
AI system in one release... Phase 1: Deterministic Readiness... Phase 2:
Consistency and Follow-Through"):

- **Phase 1 is largely done.** Requirement matrix, conditional rules (the
  "Conditional blocker" tier), a completion/lock gate, a missing-item
  report shape (`unmetChecks`/`checks`), direct field navigation, and a
  finalization blocker are all confirmed in production code.
- **Phase 3 (Voice Capture) is largely done**, ahead of the directive's own
  suggested sequencing — recording, transcription, structured extraction,
  and a review-before-apply gate all exist today.
- **Phase 4 building blocks exist** (structured findings, confidence,
  conflict surfacing) but the specific "Strength" classification and
  narrative-quality review (verbosity vs. substance, per §14) were **not
  found** — this is a genuine Phase 4 gap, not yet built.

## 3. Confirmed Real Gaps (the actual remaining work)

These are the items this pass could **not** find any existing equivalent
for, and should be treated as the true backlog — not the whole directive:

1. **"Strength" classification tier.** The existing severity model
   (Blocker/Warning/Informational/Conditional blocker) has no positive
   ("this is well documented") signal. Directive §6D and the Pre-
   Finalization Report (§7) require one.
2. **Cross-section contradiction detection** (§3, Scenario 3/4: oxygen
   contradiction, ADL-vs-narrative mismatch). No dedicated contradiction
   detector was found; today's system validates presence/completeness, not
   cross-field logical consistency.
3. **Documentation-strength / narrative-quality review** (§14, §6C): no
   evidence of a check that distinguishes "Patient declining" from a
   specific, attributable, longitudinal statement.
4. **Pre-Finalization Report as a single consolidated screen** with
   Blocking/Review Required/Improvement Suggested/Strength counts (§7) —
   Compliance & Readiness screen exists and surfaces blockers/warnings, but
   the 4-tier, single-report shape described in §7 was not confirmed as
   already built exactly this way.
5. **Requirement registry's full column set** (§22.3: Requirement ID,
   Source Authority, Jurisdiction, Effective Date, Visit Type, Role,
   Trigger, Blocking Behavior, Validation Message, Navigation Target,
   Override Permission, Report Dependency, Test Case) — `RN_ICA_REQUIRED_
  FIELD_GROUPS` + `RNICA_LOCK_READINESS_MATRIX.md` cover most of these
  informally, but not as one queryable registry with all 13 columns.
6. **Override + rationale + audit for a blocking item** (§9 "Override"):
   no override mechanism was found for the Lock gate — today a Blocker
   always blocks with no configurable/audited override path.
7. **AI-recommendation-applied/dismissed as its own audit event** —
   flagged as `[IMPLEMENTATION DISCOVERY REQUIRED]` in
   `RNICA_AI_GOVERNANCE.md` §8 already; still open.
8. **Supervisor Completion Report, Survey Readiness Report, ADR Evidence
   Report** (§15 B/D/E) — not confirmed to exist as dedicated reports;
   the closest analog found is the Billing Readiness dashboard
   (`readinessWorkflow.ts`/`readiness_dashboard_service.py`), which is a
   **different domain** (billing/RCM readiness, not clinical-documentation
   readiness) and must not be confused with or silently repurposed for
   this directive's clinical reports.
9. **Prohibited-language snapshot tests** — explicitly listed as not found
   in `RNICA_AI_GOVERNANCE.md` §9; still open.
10. **Known pre-existing open defects that intersect this directive** (from
    `RNICA_LOCK_READINESS_MATRIX.md`, already tracked, not newly
    discovered): ECOG has no enforcement branch; Fall Risk/Morse is
    blocked from becoming a Lock blocker pending authority decision; SFV
    server-side blocking enforcement not isolated; pain-reassessment
    24-hour follow-up validator not isolated from base pain screening;
    `record.status` resets to `DRAFT` on every autosave tick (may conflict
    with a future "Review Required" persisted status per item 6 in §1).

## 4. Explicit Non-Duplication Warning

Two systems in this repository are easy to confuse and must **not** be
merged or cross-wired without a deliberate decision:

- **Billing Readiness** (`readinessWorkflow.ts`, `readiness_dashboard_
  service.py`, `ReadinessWorkflowPage.tsx`) — RCM/billing-cycle readiness
  (certification, F2F, physician signature, benefit-period issues). This is
  a different product surface with its own `ReadinessStatus`/
  `OperationalBucket` types.
- **Clinical Documentation Readiness** (this directive) —
  `evaluate_finalization_readiness`, `RN_ICA_REQUIRED_FIELD_GROUPS`,
  the Compliance & Readiness screen.

They share the word "readiness" and nothing else. Any new "Documentation
Readiness Engine" work must extend the clinical-note validation engine, not
the billing readiness service.

---

## 5. Recommended Next Step

Consistent with the directive's own §21 instruction ("do not attempt to
build the entire AI system in one release") and this session's established
inventory-before-build pattern: the deterministic Phase 1/2 gaps (items 1,
2, 4, 5, 6 above) are the correct next scope — they extend
`evaluate_finalization_readiness`/`RN_ICA_REQUIRED_FIELD_GROUPS`/the
Compliance & Readiness screen that already exist, rather than building new
infrastructure. Voice capture (Phase 3) is already live and does not need
re-building. Phase 4 (AI quality review, narrative-strength scoring) is the
least-built phase and should stay last, per the directive's own sequencing.

*No code, schema, or UI change was made to produce this document.*
