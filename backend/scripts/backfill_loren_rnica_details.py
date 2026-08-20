"""Second-pass, NON-DESTRUCTIVE backfill for Loren Shields' RNICA form_data.

Only fills fields that are currently blank/empty AND have a concrete,
unambiguous value in the source HospiceMD assessment transcript
(pasted-text-dc483774-..., RN Comprehensive Nursing Assessment, visit
5/22/2024, Romel Suason RN). Treated strictly as a facts transcript, not
verbatim RN documentation -- narrative fields already populated in the
first pass are left untouched; this pass only adds concise clinical notes
distilled from the transcript, not copied prose.

IMPORTANT: many fields in the legacy export are checkbox/radio groups
whose selected option does not survive its plain-text copy/paste (all
options are listed with no marker for which was chosen). Those are
intentionally left blank here rather than guessed. See the printed
"left blank (unrecoverable from source)" report at the end.
"""

from app.core.database import SessionLocal
from app.models.rnica_assessment import RnicaAssessment

PATIENT_ID = "3885a918-7c8b-4d6d-af3a-577cc898ebdb"


def set_if_blank(container, key, value):
    """Set container[key] = value only if it's currently falsy/blank."""
    current = container.get(key)
    if current in (None, "", [], {}):
        container[key] = value
        return True
    return False


def append_note(container, key, text):
    current = (container.get(key) or "").strip()
    if text in current:
        return False
    container[key] = f"{current} {text}".strip() if current else text
    return True


def main():
    db = SessionLocal()
    try:
        rnica = (
            db.query(RnicaAssessment)
            .filter(RnicaAssessment.patient_id == PATIENT_ID)
            .first()
        )
        if not rnica:
            print("No RNICA assessment found - nothing to backfill.")
            return

        form_data = dict(rnica.form_data or {})
        changed = []

        demographics = dict(form_data.get("demographics") or {})
        if set_if_blank(demographics, "militaryService", "No"):
            changed.append("demographics.militaryService")
        form_data["demographics"] = demographics

        vitals = dict(form_data.get("vitals") or {})
        bp = dict(vitals.get("bloodPressure") or {})
        if set_if_blank(bp, "position", "Sitting"):
            changed.append("vitals.bloodPressure.position")
        vitals["bloodPressure"] = bp
        form_data["vitals"] = vitals

        cardio = dict(form_data.get("cardiovascular") or {})
        if not cardio.get("bpSymptoms"):
            cardio["bpSymptoms"] = ["Normal"]
            changed.append("cardiovascular.bpSymptoms")
        if append_note(cardio, "notes",
                       "No chest pain noted. No edema noted. BP maintained on Carvedilol "
                       "6.25mg BID and Lisinopril 10mg daily; instructed to avoid orthostatic "
                       "hypotension with position changes."):
            changed.append("cardiovascular.notes")
        form_data["cardiovascular"] = cardio

        musculo = dict(form_data.get("musculoskeletal") or {})
        if set_if_blank(musculo, "contractures",
                        "Contractures on bilateral lower extremities (BLE); severely "
                        "contracted right knee flexed toward chest, limiting positioning/comfort."):
            changed.append("musculoskeletal.contractures")
        form_data["musculoskeletal"] = musculo

        neuro = dict(form_data.get("neurological") or {})
        sleep_rest = dict(neuro.get("sleepRest") or {})
        if set_if_blank(sleep_rest, "averageSleepHours", "6-8"):
            changed.append("neurological.sleepRest.averageSleepHours")
        if append_note(sleep_rest, "notes",
                       "Per PCG, patient has uninterrupted sleep at night; no sleep issues reported."):
            changed.append("neurological.sleepRest.notes")
        neuro["sleepRest"] = sleep_rest
        form_data["neurological"] = neuro

        respiratory = dict(form_data.get("respiratory") or {})
        if append_note(respiratory, "notes",
                       "Reports SOB on minimal exertion; declines further treatment escalation, "
                       "managed with rest, positioning, and supplemental O2."):
            changed.append("respiratory.notes")
        form_data["respiratory"] = respiratory

        genitourinary = dict(form_data.get("genitourinary") or {})
        if append_note(genitourinary, "notes", "Urine clear, yellow, no odor noted."):
            changed.append("genitourinary.notes")
        form_data["genitourinary"] = genitourinary

        psychosocial = dict(form_data.get("psychosocial") or {})
        if set_if_blank(psychosocial, "distressRating", "0"):
            changed.append("psychosocial.distressRating")
        if append_note(psychosocial, "notes", "Psychosocial distress rating: None (0/10) per assessment."):
            changed.append("psychosocial.notes")
        form_data["psychosocial"] = psychosocial

        spiritual = dict(form_data.get("spiritual") or {})
        if set_if_blank(spiritual, "spiritualDistressRating", "0"):
            changed.append("spiritual.spiritualDistressRating")
        if not spiritual.get("chaplainNeeded"):
            spiritual["chaplainNeeded"] = True
            changed.append("spiritual.chaplainNeeded")
        if append_note(spiritual, "notes", "Spiritual distress rating: None (0/10) per assessment."):
            changed.append("spiritual.notes")
        form_data["spiritual"] = spiritual

        bereavement = dict(form_data.get("bereavement") or {})
        if not bereavement.get("bereavementVisitNeeded"):
            bereavement["bereavementVisitNeeded"] = True
            changed.append("bereavement.bereavementVisitNeeded")
        form_data["bereavement"] = bereavement

        referrals = dict(form_data.get("referrals") or {})
        social_work = dict(referrals.get("socialWork") or {})
        if not social_work.get("referred"):
            social_work["referred"] = True
            changed.append("referrals.socialWork.referred")
        referrals["socialWork"] = social_work
        spiritual_care = dict(referrals.get("spiritualCare") or {})
        if not spiritual_care.get("referred"):
            spiritual_care["referred"] = True
            changed.append("referrals.spiritualCare.referred")
        referrals["spiritualCare"] = spiritual_care
        form_data["referrals"] = referrals

        rnica.form_data = form_data
        db.commit()

        print(f"Backfilled {len(changed)} field(s):")
        for c in changed:
            print(" -", c)

        print(
            "\nRemaining blanks are either genuinely absent from the source assessment "
            "(e.g., height/weight/BMI, PCG name/phone -- the source itself documents "
            "'No PCG'), or are checkbox/radio selections whose chosen value does not "
            "survive the legacy system's plain-text export (e.g., lung sounds, sensory "
            "deficits, education topics taught) -- left blank rather than guessed."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
