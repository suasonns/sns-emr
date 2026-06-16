
# SNS EMR — Quality Guardrails: Future Implementation Checklist (ANTI‑DRIFT)

**Source of truth:** `SNS_EMR_QUALITY_GUARDRAILS_PLAN.md` (planned, non‑enforcing).  
**Scope:** This checklist maps the plan into deliverable steps, without changing current runtime behavior.

---

## 0) Pre‑Flight (Do this before any work)

- [ ] Confirm Alembic **current == head** (no schema drift).
- [ ] Confirm compliance guardrails are unchanged (`core_rules.md` remains supreme).
- [ ] Confirm development RLS rule remains unchanged (RLS OFF during active development).
- [ ] Confirm this work is **non‑blocking** and **non‑punitive** (no hard stops on visit duration).

---

## 1) Data Capture Foundation (No UI, no enforcement)

### 1.1 Add / confirm data fields (if not already present)

**Visits / Encounters**
- [ ] Ensure visits support explicit **time_in** and **time_out** fields.
- [ ] Ensure visits support **visit_mode** (already added) and remain compatible.
- [ ] Ensure visits can record **multiple same‑day encounters** per patient.

**Optional (metadata only)**
- [ ] Add fields to store AI capture timing (start/stop) as **non‑authoritative metadata**.

**Acceptance principle**
- [ ] Time‑in/time‑out is authoritative; AI timing is informational only.

### 1.2 Add unit calculation helper (future billing layer)
- [ ] Compute 15‑minute units using **time_in/time_out**, rounded **DOWN**.
- [ ] Store computed units as derived (not hand‑entered).

---

## 2) Tenant Toggle (Feature flag wiring only)

- [ ] Add new tenant policy flag: `quality.philosophy.enabled`.
- [ ] Default value: **OFF**.
- [ ] Store per‑tenant configuration in the existing tenant config system.

**Non‑negotiable:**
- [ ] Toggle must never affect bedside workflows.
- [ ] Toggle must never block or penalize staff.

---

## 3) QAPI / Quality Review UI (Leadership‑only)

### 3.1 Quality Philosophy display
- [ ] When `quality.philosophy.enabled = ON`, show the locked philosophy statement in:
  - QAPI review screen
  - Survey readiness / compliance summary
  - QA flag explanation panel

### 3.2 Locked text enforcement
- [ ] Statement is system‑provided, not editable.
- [ ] Statement is not injected into clinical documentation.

---

## 4) Soft QA Signals (Informational only)

### 4.1 Non‑blocking prompts
- [ ] If visit duration is unusually short (tenant configurable threshold), show a **non‑blocking reminder**:
  - “Ensure documentation reflects hospice‑level assessment and symptom review.”

### 4.2 Pattern reports (Leadership only)
- [ ] Repeated short visits by staff or by patient over time → show as a QA review item.

**Non‑negotiable:**
- [ ] No hard stops.
- [ ] No punitive language.

---

## 5) Continuous Care Support (Clinical + survey readiness)

- [ ] Allow multiple disciplines and multiple segments in the same day.
- [ ] Support RN daily assessment documentation requirement when CC continues across days.
- [ ] Support symptom‑crisis reasoning capture (crisis vs “actively dying”).

---

## 6) Exports & Evidence Pack (Survey readiness)

- [ ] Add survey evidence export section showing:
  - time_in/time_out (authoritative)
  - clinical narrative summary
  - QA review context (if enabled)

---

## 7) Tests (Required before merge)

### 7.1 Non‑blocking behavior
- [ ] Multiple visits same day are allowed.
- [ ] Short visits are allowed (no block).
- [ ] Soft QA prompt does not prevent finalization.

### 7.2 Toggle correctness
- [ ] OFF → no statement, no QA context.
- [ ] ON → statement appears in leadership views only.

### 7.3 Audit integrity
- [ ] time_in/time_out stored and preserved.
- [ ] AI timing does not override authoritative time.

---

## 8) Deployment Governance

- [ ] Document in release notes that toggle is leadership‑only.
- [ ] Provide tenant admin guide for enabling/disabling.

