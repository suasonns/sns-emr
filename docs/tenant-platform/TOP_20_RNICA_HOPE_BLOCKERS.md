# Top 20 RNICA / HOPE Blockers

**Document Status:** ARCHITECTURE CORRECTION BASELINE — produced per the
"RNICA / HOPE ARCHITECTURE CORRECTION" directive (2026-09-23). Synthesizes
`RNICA_HOPE_FIELD_MAP.md`, `RNICA_HOPE_LIFECYCLE.md`,
`HOPE_DATA_PROVENANCE_MATRIX.md`, and the four gap-analysis documents
into a single prioritized blocker list. Per the directive, HOPE
Export/Validation/Submission/Corrections/Auditability are classified as
**RNICA DEPENDENCY WORKSTREAMS**, not future enhancements — RNICA is not
complete until its output can complete the HOPE lifecycle.

Columns: Severity (CRITICAL/HIGH/MEDIUM), Owner (functional area), Dependency
(what must be true first), Required migration, Required UI change,
Required data change, Release impact.

| # | Blocker | Severity | Owner | Dependency | Required migration | Required UI change | Required data change | Release impact |
|---|---|---|---|---|---|---|---|---|
| 1 | Exported SFV fields (J2052/J2053) read the legacy self-attested RNICA-form path instead of the authoritative `SFVRequirement` completion outcome | CRITICAL | RNICA/HOPE integration | None — `SFVRequirement` already authoritative | None | Remove/replace the legacy `sfv.inPersonSfvCompleted` read path in the report/section that still displays it as if authoritative (frontend copy already corrected this session; underlying exporter read is not) | Re-point `hopeReportMapper.js` J2052/J2053 derivation at `SFVRequirement` data (fetched via existing `GET /visits/sfv-requirements`) | Release-blocking — a currently-exportable HOPE record can contradict the backend's own authoritative SFV record |
| 2 | No HOPE Generation service exists server-side; the only derivation is a browser-computed function | CRITICAL | HOPE architecture | None | Add a server-side derived-HOPE-record table/service | None required immediately, but enables all downstream stages | Enables validation, export, audit as real backend stages instead of client-only computation | Blocking for validation/export/submission (#3-#8) |
| 3 | No HOPE Validation stage exists at all — export is possible with incomplete/conflicting fields | CRITICAL | HOPE architecture | #2 (or an interim frontend-blocking check) | None | Block export/lock actions on validation failure, surface errors | Define validation rule set from `HOPE_FIELD_TRACE_MATRIX.md` gaps (incomplete response sets, missing Z0400, N0500/510/520) | Release-blocking for CMS submission readiness |
| 4 | No iQIES submission integration exists; "submission" is a free-text manual field | CRITICAL | HOPE submission | External CMS integration research (out of repository scope) | Possibly none if manual-receipt interim approach chosen | Structured receipt-entry form instead of a bare text field | Populate `RnicaHopeSubmissionAttempt` per attempt instead of overwriting single-row columns | Release-blocking for automated submission; manual workaround already functions today at reduced safety |
| 5 | `hope_validation_status`/`hope_accepted_at`/`hope_rejected_at` are dead columns — no CMS response is ever recorded | CRITICAL | HOPE submission | #4 | None (columns exist) | Display acceptance/rejection state once populated | Wire a write path from the submission-update flow | Blocks correction/resubmission (#6) entirely — no trigger condition exists |
| 6 | HOPE-level correction/resubmission (`hope_correction_required`, `hope_corrected_assessment_id`, `RnicaHopeSubmissionAttempt.supersedes_attempt_id`) is schema-only; disconnected from the working `RnicaAmendment` clinical-correction mechanism | HIGH | HOPE correction | #5 | Possibly none (columns exist) | New or extended correction UI (see `HOPE_CORRECTION_GAP_ANALYSIS.md` Option A/B decision) | Explicit product decision required: extend `RnicaAmendment` vs. build a dedicated HOPE-correction workflow | Blocking for any real-world CMS rejection to be handled in-system rather than out-of-band |
| 7 | `apply_unlock()` blocks unlocking a submitted record with no defined re-entry procedure — a dead-end once a real rejection occurs | HIGH | HOPE workflow | #5, #6 | None | Define and build the unlock-after-rejection sequence | None beyond workflow logic | Operational blocker once submission tracking becomes real |
| 8 | No `audit_event()` calls exist for any HOPE workflow transition (close/ready/export/submission-update/unlock/inactivation) or the SFV completion endpoint | HIGH | Compliance/audit | None | None (reuse existing `audit_events.py`) | None | Add `audit_event()` calls at each transition point | Compliance risk — no append-only trail exists for regulator-facing workflow actions today |
| 9 | Embedded `_by`/`_at` workflow columns are overwritten on repeat transitions, losing history (e.g. second unlock erases the first) | MEDIUM | Compliance/audit | #8 (audit log becomes the durable record) | None | None | None beyond #8 | Reduced severity once #8 lands; currently a silent history-loss risk |
| 10 | N0500/N0510/N0520 (Medications) have no live RNICA screen at all | HIGH | RNICA screen coverage | None | Possibly none (fields may already exist in schema) | Build a Medications section in `FORM_REGISTRY` | Wire `medications.*` form_data paths | Blocking for any HOPE record that requires these codes to be non-empty |
| 11 | N0500/N0510/N0520 also collide with unrelated BIMS item-code usages elsewhere in the codebase | HIGH | Data integrity | #10 | None | None | Resolve the code collision (rename internal constant or namespace) before building #10's UI | Must be resolved before #10, not after — otherwise the new UI inherits the collision |
| 12 | J2051 code-granularity mismatch: exporter emits a single `"J2051"` code while the registry declares 8 sub-codes (J2051A-H) | MEDIUM | HOPE registry/exporter consistency | None | None | None | Align exporter output granularity with registry declaration (or vice versa) | Data-format defect that would surface at real CMS validation time |
| 13 | J0050 dual-tagging conflict: two different form_data paths are both tagged item code J0050; only one is read | MEDIUM | HOPE registry hygiene | None | None | None | Remove the stale/incorrect tag from the unread path | Low operational risk today (one path already correct), but confusing for future maintainers |
| 14 | Z0400 is declared in the registry but never emitted anywhere | MEDIUM | HOPE registry hygiene | None | None | None | Either implement Z0400's source/emission or remove the declaration | Registry/reality mismatch; low risk until CMS validation checks for its presence |
| 15 | A0810 (sex/gender) response set is incomplete versus the RNICA UI's own option set (6 UI options vs. 2-value `SEX_MAP`) | MEDIUM | HOPE field mapping | None | None | Expand `SEX_MAP` (or equivalent) to cover all RNICA-collectable values | Data-loss risk on export for any patient recorded with a non-binary/other/declined value |
| 16 | A1005/A1010/A1110 (ethnicity/race/language) use `arrayText`/plain lookups with no official CMS code lookup, unlike sibling fields | MEDIUM | HOPE field mapping | None | None | Apply the same `officialCodeLookup()` pattern already used elsewhere in the mapper | Consistency and CMS-code-accuracy risk |
| 17 | A0220 (admission timepoint date) resolves via a 3-way silent fallback chain (Facesheet → RNICA order → signature date) with no indicator of which source was actually used | MEDIUM | Data provenance | None | None | Record which source populated the final value, or eliminate the fallback in favor of a single authoritative source | Provenance ambiguity risk flagged in `HOPE_DATA_PROVENANCE_MATRIX.md` |
| 18 | A0900/A0550 (DOB/ZIP) are editable in two places (Facesheet and RNICA) with no reconciliation rule | MEDIUM | Duplicate authority | None | None | Decide and enforce single-editable-source per `DUPLICATE_AUTHORITY_MATRIX.md` precedent | Same defect class as prior remediated RNICA/Facesheet duplicate-authority findings |
| 19 | `RnicaHopeSubmissionAttempt` table exists but has zero writers anywhere in the codebase — a fully-built schema doing nothing | HIGH | HOPE submission | #4, #5 | None (schema complete) | None yet | Wire creation of a row per submission attempt once #4/#5 are addressed | Represents pre-built capacity that should be reused, not re-designed, when #4/#5 are implemented |
| 20 | No CMS submission-rule validation checklist exists in the repository to define what "HOPE Validation" (#3) must actually check | HIGH | HOPE validation | External CMS specification research | N/A | N/A | Author the validation rule set itself (content, not code) as a prerequisite artifact | Blocks #3 from being scoped or estimated until this content exists |

## Summary

- **CRITICAL (5):** #1-#5 — these represent the core "RNICA is not
  complete until HOPE can complete its lifecycle" gap: a live data
  mismatch (#1), and four consecutive missing pipeline stages
  (generation, validation, submission, acceptance-recording).
- **HIGH (7):** #6, #7, #8, #10, #11, #19, #20 — correction workflow,
  audit trail, medications coverage, and the CMS-rule content
  prerequisite.
- **MEDIUM (8):** #9, #12-#18 — registry hygiene, response-set
  completeness, and provenance-ambiguity items that are real defects but
  do not block the pipeline's basic function.

## Recommended sequencing

1. Fix #1 (SFV field re-pointing) immediately — smallest, most isolated,
   highest-severity, and does not require any new architecture.
2. Resolve #11 (BIMS/medication code collision) before #10 (build the
   Medications screen), since #10's UI would otherwise inherit the
   collision.
3. Stand up #2 (server-side HOPE Generation) before attempting #3-#6,
   since validation/export/submission/correction all need a stable,
   persisted derived record to operate against rather than a
   per-render browser computation.
4. #8 (audit calls) can proceed in parallel at any time — it has no
   dependency on the others and reuses existing infrastructure.
5. #20 (CMS validation-rule content) should be authored in parallel with
   #2, since #3 cannot be scoped without it.

No redesign implementation should begin until this document, its four
supporting gap analyses, the field map, the lifecycle document, and the
provenance matrix have been reviewed and accepted, per the directive's
explicit instruction: "Do not begin a redesign until the dependency map
is complete."
