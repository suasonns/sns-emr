# J2052 / J2053 Lineage Audit

**Document Status:** PRIORITY 1 GATING DELIVERABLE — produced per the
"RNICA \u2192 HOPE CRITICAL PATH REVIEW" directive (2026-09-23). Per that
directive: "Do not proceed to larger redesign work until this trace is
complete." This document supersedes the informal "CRITICAL #1"
description in `TOP_20_RNICA_HOPE_BLOCKERS.md` with a precise,
line-referenced trace — the prior description understated one gap
(J2053) and overstated another (J2052 status is not pure legacy
self-attestation; it is actively synced, but fragile).

## Required question, answered first

**Is production HOPE export still reading legacy RNICA self-attestation
fields? YES / NO**

**YES, partially — the two fields do not have the same answer:**

- **J2052 (completion status/date): PARTIALLY.** The exported field
  (`sfv.inPersonSfvCompleted`, `sfv.sfvDate`) is a `form_data` field on
  the *triggering* RNICA record, but it is **actively kept in sync**
  with the authoritative backend `SFVRequirement` record via a
  client-side effect that re-fetches on every RNICA-screen load (detail
  below). It is not abandoned legacy self-attestation, but it is a
  **fragile, pull-based, best-effort sync**, not a direct read of the
  authoritative source at export time.
- **J2053 (SFV symptom impact): YES, unambiguously.** There is **no
  capture path for J2053 on the completion visit at all.** The only UI
  that can write `symptomImpactAtSfv.*` is a set of radio-button fields
  inside the RNICA form's own `sfv` section (`RNICA.jsx:9517-9525`) —
  i.e. still entered on (or near) the triggering document, not the
  separate completion encounter. `VisitNotes.jsx`'s
  `SymptomFollowUpVisitSection` (the correct, separate-visit completion
  UI) calls only `completeSfvRequirement(requirementId, visitId)`
  (`VisitNotes.jsx:1062`) — a bare `{ completionVisitId }` payload,
  confirmed against the API contract itself
  (`sns-emr-frontend/src/api/sfv.ts`, `completeSfvRequirement()`) — it
  never sends symptom-impact data. **There is currently no way to
  document J2053 through the authoritative separate-visit completion
  workflow.**

## J2052 — full trace

| Stage | Current | File:line |
|---|---|---|
| **Trigger source** | `symptomImpact.*` (J2051 values) evaluated for moderate/severe | `hopeReportMapper.js:394-411` (`getSfvStatus`); backend independently: `hope_phase_b_engine.py` |
| **Authoritative completion record** | `SFVRequirement` row: `completed_visit_id`, `status`, `completed_at` | `backend/app/models` (SFVRequirement); enforced via `complete_sfv_requirement_from_visit()`, `hope_phase_b_engine.py:397-438` |
| **Completion API** | `POST /visits/sfv-requirements/{id}/complete` — accepts only `{ completionVisitId }`; server derives clinician/tenant/patient authorization | `backend/app/api/visits.py`; client wrapper `sfv.ts::completeSfvRequirement` |
| **Sync into RNICA form_data (current storage)** | `SfvStatusCard` fetches `GET /visits/sfv-requirements?patientId=...` on every mount of the RNICA `sfv` section; if the most-recently-completed requirement is found, it calls `onSyncCompletionStatus(completed, completedAt)`, which sets `form_data.sfv.inPersonSfvCompleted` and `form_data.sfv.sfvDate` on the **triggering** RNICA record | `RNICA.jsx:7959-7979` (fetch + sync logic), `:8401-8404` (the callback writing `u("inPersonSfvCompleted", completed)` / `u("sfvDate", completedAt)`) |
| **Mapper (export read)** | Reads `sfv.inPersonSfvCompleted`, `sfv.sfvDate`, `sfv.reasonNotCompleted` directly off `form_data.sfv` | `hopeReportMapper.js:618` |
| **Model** | No backend HOPE object exists; the export read is entirely client-side against the same `form_data` blob the RNICA screen edits | N/A — see `RNICA_HOPE_LIFECYCLE.md` (no server-side HOPE Generation) |
| **Serializer** | None — `hopeReportMapper.js` is the only transform, invoked directly by `HopeReport.jsx`/`ComplianceHopeBoard.jsx` | `HopeReport.jsx:13,162`; `ComplianceHopeBoard.jsx:9,416` |
| **Exporter / Output** | On-screen report + `window.print()`; no file/XML artifact (see `HOPE_EXPORT_GAP_ANALYSIS.md`) | `HopeReport.jsx:214` |

### J2052 gap analysis

| Field | Current source | Current transform | Current storage | Expected source | Expected export logic | Mismatch | Risk | Fix required |
|---|---|---|---|---|---|---|---|---|
| J2052.A (In-person SFV completed?) | `SfvStatusCard` sync effect, from `GET /visits/sfv-requirements` | Pull-based sync on RNICA-screen mount only | `form_data.sfv.inPersonSfvCompleted` (denormalized copy) | `SFVRequirement.status == "COMPLETED"` read directly at export/generation time | A server-side HOPE Generation step should read `SFVRequirement` directly, not a denormalized copy | The exported value is a **cached copy**, correct only if the RNICA record was reopened (and thus re-synced) after completion; a HOPE Generation/export run that does **not** go through the RNICA screen (e.g. a future batch export job) has no equivalent sync path and would read a stale value | MEDIUM — currently masked because export today only happens via the on-screen report, which the sync effect always runs before render; becomes HIGH the moment export is automated/server-side, because there is no non-UI sync path | Re-point the (future) server-side HOPE Generation service at `SFVRequirement` directly; do not rely on the `form_data.sfv.*` denormalized copy for this field once a server-side generator exists |
| J2052.B (Date) | Same sync effect (`latest.completedAt.slice(0,10)`) | Same | `form_data.sfv.sfvDate` | `SFVRequirement.completed_at` | Same as above | Same as above | Same as above | Same as above |
| J2052.C (Reason not completed) | **Manually typed** free-text field, `reasonNotCompleted` | None — direct user entry on the RNICA `sfv` section | `form_data.sfv.reasonNotCompleted` | Not currently backed by any `SFVRequirement` field (no "reason" column found on that model in this pass) | Undetermined — requires a product decision on whether "reason not completed" belongs on `SFVRequirement` (e.g. an `OVERDUE`/`CANCELLED` reason) or remains a RNICA-form annotation | This field has **no sync mechanism at all** — it is pure self-attestation with no authoritative backend counterpart to reconcile against | MEDIUM — low volume (only relevant when SFV is NOT completed), but currently unverifiable against any system-of-record | Add a `reason`/`cancellation_reason` field to `SFVRequirement` if this must be authoritative, or explicitly document it as a RNICA-only annotation not subject to the single-source rule |

## J2053 — full trace

| Stage | Current | File:line |
|---|---|---|
| **Intended source (per architecture)** | Completion visit's clinical documentation (a genuinely separate encounter) | N/A — does not exist yet |
| **Actual source today** | RNICA form's own `sfv` section, radio fields `symptomImpactAtSfv.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | `RNICA.jsx:9518-9525` |
| **Reachability of that UI** | `"sfv"` is a registered `FORM_REGISTRY` section (`RNICA.jsx:249-256`) and is **not** in `UPDATE_HIDDEN_ROUTE_KEYS`'s admission-mode gating — it renders in the same navigable set as any other RNICA section on an admission assessment; it is only hidden from the sidebar/route in **update-mode** RNICA visits (`RNICA.jsx:258-259`) | `RNICA.jsx:249-259` |
| **Completion-visit capture path** | **Does not exist.** `SymptomFollowUpVisitSection` (`VisitNotes.jsx`) sends only `{ completionVisitId }` | `VisitNotes.jsx:1062`; `sfv.ts::completeSfvRequirement` |
| **Mapper (export read)** | `symptomEntries(sfv.symptomImpactAtSfv || {})` — reads directly off the RNICA record's `form_data.sfv.symptomImpactAtSfv` | `hopeReportMapper.js:619` |
| **Model / Serializer / Exporter / Output** | Same as J2052 (no backend HOPE object; no file artifact) | — |

### J2053 gap analysis

| Field | Current source | Current transform | Current storage | Expected source | Expected export logic | Mismatch | Risk | Fix required |
|---|---|---|---|---|---|---|---|---|
| J2053.A-H (Pain/SOB/Anxiety/Nausea/Vomiting/Diarrhea/Constipation/Agitation impact at SFV) | RNICA form's `sfv` section radio fields, editable on the **triggering RNICA record itself** | Direct passthrough, no derivation | `form_data.sfv.symptomImpactAtSfv.*` on the triggering RNICA record | The separate, later, qualifying completion visit's clinical documentation | A server-side HOPE Generation step should read symptom-impact-at-SFV data attached to the **completion visit** (a field that does not yet exist on `Visit`/`SFVRequirement`) | **CRITICAL** — this is architecturally backwards: the value that is supposed to represent the outcome of the separate follow-up encounter can currently only be entered on the triggering document, and the actual separate-visit completion workflow has no field for it at all | **CRITICAL** — a clinician completing an SFV through the correct workflow (`VisitNotes.jsx`) has no way to record J2053 at all today; if they instead go back and edit the RNICA `sfv` section's radio fields, they are documenting the follow-up's clinical findings on the wrong encounter, which is exactly the anti-pattern the separate-visit rule (`triggerVisitId != completionVisitId`) was designed to prevent for J2052 | Add symptom-impact-at-SFV fields to the completion workflow (`SymptomFollowUpVisitSection` in `VisitNotes.jsx`, plumbed through a new/extended `SFVRequirement` or `Visit` field and a corresponding backend acceptance in the completion endpoint), and remove (or clearly mark historical-only) the `symptomImpactAtSfv.*` fields still editable on the RNICA triggering form |

## Summary verdict

| Item | Verdict |
|---|---|
| J2052 completion status/date | Synced from authoritative source today, but via a fragile pull-based mechanism with no non-UI path; correct architecture requires the future server-side HOPE Generation service to read `SFVRequirement` directly instead of the denormalized `form_data.sfv.*` copy |
| J2052 "reason not completed" | Pure self-attestation, no authoritative backend counterpart exists to sync against |
| J2053 (all 8 sub-fields) | **No completion-visit capture path exists at all.** This is the single most severe finding in this audit — more severe than the prior "CRITICAL #1" description implied, because it is not merely "reading a stale/legacy field," it is "the correct field genuinely cannot be populated through the correct workflow today." |

## Required fix (before any larger redesign work, per directive)

1. **Immediate, isolated fix for J2052:** none required at the data-
   correctness level for the current UI-driven export path (the sync
   already works); document the fragility (no non-UI sync path) as a
   prerequisite condition for the future server-side HOPE Generation
   service (do not build a second denormalization).
2. **Required before J2053 can be considered fixed:** a product/schema
   decision on where symptom-impact-at-SFV data is captured on the
   completion visit (extend `SFVRequirement` with an impact payload, or
   attach it to the completion `Visit`'s own clinical documentation
   fields), plus the corresponding completion-endpoint and
   `SymptomFollowUpVisitSection` UI changes to capture it there instead
   of on the triggering RNICA form.
3. This document does not implement either fix — per directive, "do not
   proceed to larger redesign work until this trace is complete." This
   trace is now complete; implementation is a distinct next step
   requiring explicit approval.
