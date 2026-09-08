# Manual Demo Validation Checklist — RNICA Legacy Writer Removal

Use this to manually confirm, in your own browser, what automated tooling in
this session could not complete live (see
`docs/planning/rnica_legacy_writer_removal_verification.md` for why).

Branch: `feature/production-hnp-clinical-runtime`
Commits under test: `8fde005`, `f93988a`, `ab5e262`

Before starting, confirm both dev servers are running:
- Backend: `http://localhost:8000/health` → `{"status":"ok",...}`
- Frontend: `http://localhost:5173/` loads the login page

Login: `rsuason@loveandfaithhospice.com` / `LoveFaithHospice2026!`

For each item below, check it off only after you've actually seen it on
screen — do not assume a prior pass carries forward.

---

## Section 1 — Loren

Patient ID: `3ea2f6fa-8dd9-4e3c-9b7d-009ddbe17ab0`

- [ ] Open Loren's chart
- [ ] Open RNICA / Finalization
- [ ] Verify PPS is visible
- [ ] Verify KPS is visible
- [ ] Verify NYHA is visible
- [ ] Verify each scale has a readable clinical interpretation (not just a
      raw number)
- [ ] Click "Build Draft from Documented Findings" (or "Replace with New
      Draft" if a narrative already exists)
- [ ] Confirm the generated narrative contains **no** legacy headings
      (`HOSPICE CLINICAL PICTURE`, `REASON FOR HOSPICE ADMISSION`,
      `EVIDENCE OF DECLINE`, `DISEASE-SPECIFIC SUPPORT`)
- [ ] Confirm the Narrative Quality Gate shows PASS
- [ ] Make a small manual edit to the narrative text
- [ ] Save
- [ ] Reload the page (hard refresh)
- [ ] Confirm the manual edit is still present after reload

## Section 2 — Norma

Patient ID: `53fe69e1-fcd5-4b49-8203-9b890b18b7d6` · RNICA assessment
`cb060604-405d-4b09-b4dc-e313542d4a31`

- [ ] Open Norma's chart
- [ ] Open RNICA / Finalization
- [ ] Verify PPS shows 20%
- [ ] Verify KPS shows 20
- [ ] Verify ECOG shows 4
- [ ] Verify each scale has a readable clinical interpretation
- [ ] Click "Build Draft from Documented Findings" / "Replace with New Draft"
- [ ] Confirm the generated narrative contains **no** legacy headings
- [ ] Confirm no raw internal IDs, field-key names, or source filenames
      appear in the prose
- [ ] Confirm the Narrative Quality Gate shows PASS
- [ ] Make a small manual edit to the narrative text
- [ ] Save
- [ ] Reload the page (hard refresh)
- [ ] Confirm the manual edit is still present after reload

## Section 3 — Kessler

Patient ID: `ba24830e-19f8-4b84-bbf3-e88374a6db25` · RNICA assessment
`5d39cc37-19a2-4e83-a1dc-46c8dcefc94b`

- [ ] Open Kessler's chart
- [ ] Open RNICA / Finalization
- [ ] Verify FAST is visible
- [ ] Verify FAST has a readable clinical interpretation
- [ ] Click "Build Draft from Documented Findings" / "Replace with New Draft"
- [ ] Confirm the generated narrative contains **no** legacy headings
- [ ] Confirm the Narrative Quality Gate shows PASS
- [ ] Make a small manual edit to the narrative text
- [ ] Save
- [ ] Reload the page (hard refresh)
- [ ] Confirm the manual edit is still present after reload

## Section 4 — New (unsaved) assessment — the decisive regression check

This is the specific path the legacy writer used to occupy. This section
confirms it is truly gone, not just unreachable in the three regression
patients above.

- [ ] Start a new RN assessment for any disposable/test patient
- [ ] Enter a few findings (do **not** save yet)
- [ ] Click "Build Draft from Documented Findings"
- [ ] Confirm **no** narrative is generated
- [ ] Confirm a jargon-free message appears explaining the assessment must
      be saved first (not a raw error or stack trace)
- [ ] Confirm all previously entered findings are still present on screen
      (nothing was cleared)
- [ ] Confirm a "Save Assessment" button/action is available
- [ ] Click "Save Assessment"
- [ ] Confirm a valid assessment ID is now associated with the record
- [ ] Click "Build Draft from Documented Findings" again
- [ ] Confirm this time it calls the backend and a V2 draft appears
- [ ] Confirm the draft contains **no** legacy headings

---

## Section 5 — Deployment decision

Based on the results above, circle one:

- [ ] **PASS** — all sections fully checked, no issues found
- [ ] **PASS WITH LIMITATIONS** — note limitations below
- [ ] **FAIL** — note blocking issues below

Notes / limitations / issues found:

```
(fill in during manual validation)
```
