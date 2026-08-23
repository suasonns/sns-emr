# Disposition: `rnica-poc-lock-no-autogen` (archived)

**Status:** Archived. Remote branch deleted; former tip preserved via annotated tag
`archive/rnica-poc-lock-no-autogen-final` pointing at commit
`3cc32dbd36da9164988eee4390443288f3ca9ea1`.

**Recovery method used:** the local worktree's own `refs/heads/rnica-poc-lock-no-autogen`
ref (not yet garbage-collected) still held the exact former branch tip after the remote
delete. Verified via `git log -1 refs/heads/rnica-poc-lock-no-autogen` and cross-checked
against the reflog (`git reflog --all`), which shows the same SHA `3cc32db` as the last
commit reachable on that branch. No GitHub API event lookup was necessary because the
local ref recovery was authoritative and exact.

**Base for comparison:** `rnica-facesheet-clean` (current integration branch, at the time
of this analysis `b642488`, before the PR #10 lint merge).

## Unique commits (25) and disposition

Every commit below is unique to `rnica-poc-lock-no-autogen` (`git log <tip> --not
rnica-facesheet-clean`). Each was checked by extracting the distinctive field
path(s)/config strings/function calls it introduced and grepping those exact strings
against the current integrated `RNICA.jsx` / backend to confirm presence or absence.

| Commit | Summary | Disposition | Evidence |
|---|---|---|---|
| `3cc32db` | §5.1 Neuro/Mental/Sensory gaps | **Superseded** | `symptomsDemeanor` and related §5.1 field paths present in current `RNICA.jsx` |
| `eabfdcf` | §5.10 Musculoskeletal gaps | **Superseded** | `romLimitations` present in current `RNICA.jsx` |
| `f5b2984` | Somnolence option, Sleep Pattern §5.9 | **Superseded** | Somnolence option present under `sleepRest` in current `RNICA.jsx` |
| `cc19f98` | §5.9 Sleep/Rest fields | **Superseded** | `sleepRest.nighttimeSymptoms` present |
| `dbbb8cb` | §5.8 GU/Reproductive fields | **Superseded** | `catheter.irrigation.solution` present |
| `bdace7f` | §5.5 GI fields | **Superseded** | corresponding GI field paths present |
| `bb59cea` | §5.3 Respiratory fields | **Superseded** | corresponding Respiratory field paths present |
| `eeb5d68` | §5.2 Cardiovascular fields | **Superseded** | `pulseSites` present |
| `a978cab` | §5.7 Endocrine fields | **Superseded** | `diabetes.oralHypoglycemics` present |
| `b9bad73` | §5.4 Immunological/Infection fields | **Superseded** | `antibioticResistantInfection` present |
| `a124e6f` | §5.11 Skin/Wound fields | **Superseded** | `pressureReliefMeasures` present |
| `d87ac7e` | Remove forced POC auto-gen from lock (CHECK 2) | **Superseded (correction already applied)** | `generate_and_apply_poc_from_assessment` confirmed NOT called from `visits.py` lock path in current code; test `test_lock_rnica_assessment_creates_no_poc_version_or_problem` present and passing in `test_rnica_poc_adapter.py` |
| `f2b5ec3` | POC controls on Imminent Death (J0050) | **Superseded** | `"imminentDeath"` present in current `BODY_SYSTEM_SECTIONS` set |
| `d5b26ad` | Body-system POC controls + Nutrition NPO/feeding fields | **Superseded** | corresponding Nutrition field paths present in current `RNICA.jsx`; test `test_update_and_resolve_require_explicit_action` present |
| `c3e9428` | Physician Identity Mapping fail-closed linkage | **Superseded** | `test_physician_identity_mapping.py` present, passing, in current 363-test suite |
| `b4d9fe2` | Provider Signature Authority Model | **Superseded** | primary/alternate-signer authority tests present in `test_physician_orders_lifecycle.py` |
| `9922c00` | F2F Phase 1 lifecycle rebuild | **Superseded** | `test_f2f_lifecycle.py` present, passing |
| `6c56bb9` | CTI Phase 1 lifecycle rebuild | **Superseded** | `test_cti_lifecycle.py` present, passing |
| `51f7490` | Physician Orders Phase 1 lifecycle expansion | **Superseded** | `test_physician_orders_lifecycle.py` present, passing |
| `1c8de6e` | Split MD-signature widget (oversight/signer/follow-up) | **Superseded** | current signature-authority UI/tests reflect the split |
| `d7789a5` | Fix signing-authority gap (Admin/DPCS could sign orders) | **Superseded** | `test_idg_batch_sign_authorization.py` present, passing, covering this exact authorization gap |
| `88481c8` | Widget-visibility engine extension for Compliance/QA; dev CORS fix | **Superseded** | `test_dashboard_widget_visibility.py` present, passing |
| `880bf87` | Render compliance_queue widgets on tenant dashboard | **Superseded (superseding rewrite)** | current `DashboardOverview.jsx` is a larger, different, superseding implementation (diffstat) |
| `428f5d7` | Role-aware compliance dashboard widgets + persistent branding | **Superseded (superseding rewrite)** | same as above |
| `c7b2820` | Code Status/Physician/Contact shared-model sync + layout fix | **Superseded** | corresponding shared-model sync present in current `patient_code_status.py`/`patient_contact.py` models |

## Conclusion

All 25 unique commits' functionality is present in `rnica-facesheet-clean` today, either
verbatim (field paths/tests still exist) or via a superseding rewrite (dashboard widgets).
No missing required behavior was identified. The branch was safe to archive. The tag
`archive/rnica-poc-lock-no-autogen-final` preserves the exact former history for future
audit if needed; nothing was deleted without a recoverable pointer.
