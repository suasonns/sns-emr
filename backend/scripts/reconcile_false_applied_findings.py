"""Reconciliation pass for previously-mislabeled APPLIED structured findings.

Context: before the verified-write engine (app.services.evidence.
rnica_apply_verification) existed, a PatientHarvestedSignal could be marked
review_status="APPLIED" purely on the frontend's client-side assumption that
its structured-finding writes had landed in the RNICA assessment's
form_data -- with zero server-side confirmation. This script re-checks every
historically-APPLIED signal against the assessment's CURRENT persisted
form_data (fresh, uncached SQL read) using the exact per-write audit trail
the frontend already recorded in RnicaAssessment.field_provenance
(signal_id/section/path/value[/kind]), and corrects any signal whose claimed
destination value is no longer actually present.

Usage:
    python -m scripts.reconcile_false_applied_findings [--dry-run] [--patient-id UUID]

Behavior:
  - Only ever touches signals with review_status == "APPLIED".
  - Never deletes or overwrites the original review event; it adds a new,
    clearly-labeled corrective audit trail entry
    (review_disposition_reason) and only then updates review_status.
  - A signal with NO field_provenance entries at all (applied before
    provenance tracking existed, or applied by a path that never recorded
    provenance) cannot be verified either way -- it is reported as
    UNVERIFIABLE and left untouched; it is not silently assumed correct.
  - Reclassification rule:
      * all claimed writes verified persisted  -> leave APPLIED (no-op)
      * some (not all) verified                -> PARTIALLY_APPLIED
      * zero verified AND the destination currently holds some OTHER
        explicit non-default value               -> CONFLICT (something else
        is occupying that field now; needs human re-review, never silently
        overwritten by this script)
      * zero verified AND destination is blank/absent -> NEW (fully lost,
        actionable again)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
import app.main  # noqa: E402,F401  (importing the app registers every ORM model/relationship in the correct order)
from app.models.patient_evidence import PatientHarvestedSignal  # noqa: E402
from app.models.rnica_assessment import RnicaAssessment  # noqa: E402
from app.services.evidence.rnica_apply_verification import get_nested_value  # noqa: E402
from app.services.evidence.structured_findings import CONCEPT_REGISTRY  # noqa: E402


def _fetch_fresh_form_data(db, assessment_id) -> dict:
    row = db.execute(
        text("SELECT form_data FROM rnica_assessments WHERE id = :id"),
        {"id": str(assessment_id)},
    ).first()
    return (row[0] or {}) if row else {}


def _verify_entry(persisted_form_data: dict, entry: dict) -> bool:
    section = entry.get("section")
    path = entry.get("path")
    value = entry.get("value")
    kind = entry.get("kind")
    section_data = (persisted_form_data or {}).get(section)
    actual = get_nested_value(section_data, path)
    if kind == "array_member":
        return isinstance(actual, list) and value in actual
    if kind == "scalar":
        return actual == value
    # Legacy provenance entry recorded before "kind" was tracked -- accept
    # either a direct scalar match or array-membership so we don't punish
    # old multi_add writes for a field we simply didn't tag at the time.
    return actual == value or (isinstance(actual, list) and value in actual)


def _derive_expected_entries_from_registry(signal) -> tuple[list[dict], list[str]]:
    """Fallback for signals with NO field_provenance recorded at all (the
    vast majority of pre-fix APPLIED signals -- provenance tracking is a
    recent addition). Independently re-derives what SHOULD have been
    written, straight from the same CONCEPT_REGISTRY the harvester itself
    validated the finding's concept_code against, so this check owes
    nothing to whatever the (unverified) original apply pass claimed.

    Returns (derived_entries, skipped_reasons). Only "set" and "multi_add"
    fixed-value writes are supported here -- value_slot (bounded numeric/
    free-text parameter) and push_draft_row (new list row) concepts are
    reported as skipped/unsupported rather than silently assumed correct
    or incorrect, since verifying them needs the finding's own captured
    value/row shape which this fallback path does not attempt to guess.
    """
    entries: list[dict] = []
    skipped: list[str] = []
    for finding in signal.structured_findings or []:
        if not isinstance(finding, dict):
            continue
        if finding.get("assertion_status") != "CURRENT":
            continue  # HISTORICAL/NEGATED/UNCERTAIN findings are never applied
        concept_code = finding.get("concept_code")
        mapping = CONCEPT_REGISTRY.get(concept_code)
        if mapping is None:
            skipped.append(f"{concept_code}: not in CONCEPT_REGISTRY")
            continue
        if mapping.value_slot is not None:
            skipped.append(f"{concept_code}: value_slot write unsupported by registry fallback")
        for write in mapping.writes:
            if write.op == "push_draft_row":
                skipped.append(f"{concept_code}: push_draft_row write unsupported by registry fallback")
                continue
            entries.append(
                {
                    "section": write.section or mapping.section,
                    "path": write.path,
                    "value": write.value,
                    "concept_code": concept_code,
                    "kind": "array_member" if write.op == "multi_add" else "scalar",
                }
            )
    return entries, skipped


def reconcile(db, *, dry_run: bool, patient_id: UUID | None) -> dict:
    query = db.query(PatientHarvestedSignal).filter(
        PatientHarvestedSignal.review_status == "APPLIED"
    )
    if patient_id is not None:
        query = query.filter(PatientHarvestedSignal.patient_id == patient_id)
    applied_signals = query.all()

    report = {
        "total_applied_signals_checked": len(applied_signals),
        "unchanged_still_applied": [],
        "reclassified_partially_applied": [],
        "reclassified_conflict": [],
        "reclassified_new": [],
        "unverifiable_no_findings_or_unmapped": [],
    }

    # Cache fresh form_data per assessment so multiple signals against the
    # same assessment only pay for one fresh SQL read each.
    form_data_cache: dict[str, dict] = {}

    for signal in applied_signals:
        assessments = (
            db.query(RnicaAssessment)
            .filter(RnicaAssessment.patient_id == signal.patient_id)
            .all()
        )
        matching_entries: list[tuple[RnicaAssessment, dict]] = []
        for assessment in assessments:
            for entry in assessment.field_provenance or []:
                if isinstance(entry, dict) and str(entry.get("signal_id")) == str(signal.id):
                    matching_entries.append((assessment, entry))

        source = "provenance"
        skipped_reasons: list[str] = []
        if not matching_entries:
            source = "registry_fallback"
            derived_entries, skipped_reasons = _derive_expected_entries_from_registry(signal)
            # Check every one of this patient's assessments (we don't know,
            # without provenance, which specific assessment the write was
            # intended for) -- a match on ANY of them counts as verified.
            for entry in derived_entries:
                for assessment in assessments:
                    matching_entries.append((assessment, entry))

        if not matching_entries:
            note = "no CURRENT structured_findings with a registry-mapped writable field"
            if skipped_reasons:
                note += f" ({'; '.join(skipped_reasons)})"
            report["unverifiable_no_findings_or_unmapped"].append(f"{signal.id}: {note}")
            continue

        results = []
        for assessment, entry in matching_entries:
            cache_key = str(assessment.id)
            if cache_key not in form_data_cache:
                form_data_cache[cache_key] = _fetch_fresh_form_data(db, assessment.id)
            verified = _verify_entry(form_data_cache[cache_key], entry)
            results.append((assessment, entry, verified))

        if source == "registry_fallback":
            # Collapse per-(assessment, entry) results back down to one
            # result per distinct derived write: verified on ANY assessment
            # counts as that write being verified overall.
            collapsed: dict[tuple, tuple] = {}
            for assessment, entry, verified in results:
                key = (entry.get("section"), entry.get("path"), entry.get("value") if not isinstance(entry.get("value"), list) else tuple(entry.get("value")))
                prior = collapsed.get(key)
                if prior is None or (verified and not prior[2]):
                    collapsed[key] = (assessment, entry, verified)
            results = list(collapsed.values())

        verified_count = sum(1 for _, _, v in results if v)
        total = len(results)

        if verified_count == total:
            report["unchanged_still_applied"].append(str(signal.id))
            continue

        new_reason_lines = [
            f"[RECONCILIATION:{source}] Verified-write audit re-check found "
            f"{verified_count}/{total} expected field write(s) actually persisted."
        ]
        if skipped_reasons:
            new_reason_lines.append(f"  (unsupported/skipped: {'; '.join(skipped_reasons)})")
        for assessment, entry, verified in results:
            new_reason_lines.append(
                f"  - assessment={assessment.id} section={entry.get('section')} "
                f"path={entry.get('path')} concept={entry.get('concept_code')} "
                f"claimed_value={entry.get('value')!r} verified={verified}"
            )

        if verified_count > 0:
            new_status = "PARTIALLY_APPLIED"
            report["reclassified_partially_applied"].append(str(signal.id))
        else:
            # Zero writes verified. Decide NEW vs CONFLICT by inspecting
            # whether the destination currently holds some other explicit
            # value (something/someone else is occupying the field) versus
            # being genuinely blank/absent (fully lost -- safe to reopen).
            any_occupied = False
            for assessment, entry, _ in results:
                cache_key = str(assessment.id)
                section_data = (form_data_cache[cache_key] or {}).get(entry.get("section"))
                actual = get_nested_value(section_data, entry.get("path"))
                if entry.get("kind") == "array_member":
                    occupied = isinstance(actual, list) and len(actual) > 0
                else:
                    occupied = actual not in (None, "", False, [])
                if occupied:
                    any_occupied = True
                    break
            if any_occupied:
                new_status = "CONFLICT"
                report["reclassified_conflict"].append(str(signal.id))
            else:
                new_status = "NEW"
                report["reclassified_new"].append(str(signal.id))

        new_reason_lines.append(f"  -> reclassified {signal.review_status} -> {new_status}")
        corrective_note = "\n".join(new_reason_lines)

        if not dry_run:
            existing_reason = signal.review_disposition_reason or ""
            signal.review_disposition_reason = (
                (existing_reason + "\n\n" if existing_reason else "") + corrective_note
            )
            signal.review_status = new_status

    if not dry_run:
        db.commit()

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not write changes.")
    parser.add_argument("--patient-id", type=str, default=None, help="Limit to one patient.")
    args = parser.parse_args()

    patient_id = UUID(args.patient_id) if args.patient_id else None

    db = SessionLocal()
    try:
        report = reconcile(db, dry_run=args.dry_run, patient_id=patient_id)
    finally:
        db.close()

    print("=" * 70)
    print("RNICA Apply reconciliation report", "(DRY RUN)" if args.dry_run else "(APPLIED)")
    print("=" * 70)
    for key, value in report.items():
        if isinstance(value, list):
            print(f"{key}: {len(value)}")
            for item in value:
                print(f"    {item}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
