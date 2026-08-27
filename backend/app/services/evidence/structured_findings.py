"""Shared StructuredFinding contract for AI -> RNICA structured-field mapping.

Both AI extraction pipelines (the document/note harvester in
ai_extraction_service.py, and the visit-recording transcript drafter in
note_draft_service.py) can propose that a specific RNICA checkbox/dropdown/
radio control be populated from evidence. Rather than letting either model
emit an arbitrary field_path/value pair (which would mean trusting the LLM
to know the exact RNICA schema and never hallucinate a bogus path/value),
BOTH pipelines emit only a fixed, closed vocabulary of clinical "concepts"
(e.g. RESP_OXYGEN_NASAL_CANNULA). This module is the single source of truth
for:
    - the StructuredFinding contract both pipelines must return
    - CONCEPT_REGISTRY: the fixed concept_code -> RNICA field(s) mapping
    - validation that discards anything not an exact, server-recognized
      concept/value

The frontend (RNICA.jsx) keeps its own mirror of CONCEPT_REGISTRY (kept in
lockstep by convention, same pattern as AI_SECTION_NOTE_TARGETS /
ALLOWED_CLINICAL_SYSTEMS_BY_DISCIPLINE elsewhere in this codebase) because
formData lives client-side -- this module's job is only to validate what a
model is allowed to assert, never to write into a chart itself.

Non-negotiable rules (same family as ai_extraction_service.py /
note_draft_service.py):
    - NEVER let a model emit a field_path/value directly -- only a
      recognized concept_code from CONCEPT_REGISTRY is accepted; anything
      else is discarded.
    - NEVER apply a HISTORICAL, NEGATED, or UNCERTAIN finding to a current-
      status control -- those are only ever surfaced for clinician review,
      never auto-applied (the frontend enforces this too, but concepts are
      designed so only CURRENT+asserted findings have any effect at all).
    - NEVER invent a value outside a concept's own fixed vocabulary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

SOURCE_TYPES = {"TRANSCRIPT", "REFERRAL_HNP", "UPLOADED_DOCUMENT", "CLINICAL_NOTE"}
ASSERTION_STATUSES = {"CURRENT", "HISTORICAL", "NEGATED", "UNCERTAIN"}
SUBJECTS = {"PATIENT", "FAMILY", "OTHER"}


@dataclass(frozen=True)
class StructuredFinding:
    """One validated, concept-coded candidate structured-field value.

    Never auto-applied by this module -- only validated. Application (with
    blank-only / no-overwrite / provenance rules) happens client-side.
    """

    concept_code: str
    value: Any  # True for a pure presence concept, or the concept's bounded parameter (e.g. liters/min, wound location)
    source_type: str
    source_excerpt: str
    confidence: float | None
    assertion_status: str
    subject: str
    source_record_id: str | None = None
    source_date: str | None = None
    source_location: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_code": self.concept_code,
            "value": self.value,
            "source_type": self.source_type,
            "source_record_id": self.source_record_id,
            "source_excerpt": self.source_excerpt,
            "source_date": self.source_date,
            "source_location": self.source_location,
            "confidence": self.confidence,
            "assertion_status": self.assertion_status,
            "subject": self.subject,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
        }


@dataclass(frozen=True)
class ValueSlot:
    """Describes the bounded secondary parameter a concept may accept
    (e.g. the liters/min number for an oxygen-delivery concept, or the
    anatomic location string for a wound-present concept). Concepts with no
    value_slot are pure presence facts -- `value` must be truthy to apply.
    """

    kind: str  # "numeric" | "free_text_bounded"
    path: str  # dotted field path (relative to the concept's section) this parameter is written to
    min_value: float | None = None
    max_value: float | None = None
    max_len: int | None = None


@dataclass(frozen=True)
class FieldWrite:
    path: str  # dotted field path relative to the write's section
    value: Any  # fixed value written whenever this concept is accepted
    op: str = "set"  # "set" (scalar/boolean) | "multi_add" (append to array if array still blank-owned) | "push_draft_row" (append a new row to a list-of-records field)
    # Almost every concept writes only within its own declared `section`.
    # A handful of clinical facts legitimately belong on more than one
    # chart section at once (e.g. a hemiparesis finding is both a
    # neurological deficit AND a musculoskeletal disability
    # classification) -- set `section` to override just that one write's
    # destination section instead of forcing a second, duplicate concept.
    section: str | None = None


@dataclass(frozen=True)
class ConceptMapping:
    concept_code: str
    section: str
    label: str
    writes: tuple[FieldWrite, ...] = ()
    value_slot: ValueSlot | None = None
    # For push_draft_row concepts, the shape of the new row (besides the
    # value_slot's own path, e.g. "location") -- all other row fields are
    # deliberately left blank so the model can never invent stage/size/
    # drainage/treatment details it wasn't given.
    draft_row_field: str | None = None


def _fw(path: str, value: Any, op: str = "set", section: str | None = None) -> FieldWrite:
    return FieldWrite(path=path, value=value, op=op, section=section)


# ---------------------------------------------------------------------------
# CONCEPT REGISTRY -- the ONLY vocabulary either AI pipeline may assert.
#
# Scope, per explicit product direction: FULL field coverage (not a sample)
# for the 8 highest-confidence sections -- performanceStatus, cardiovascular,
# respiratory, neurological, infection, skin, nutrition, musculoskeletal --
# for every field whose value is a closed enum/multi-select/boolean AND is
# realistically something a clinician would state or document in prose
# (a fact, not a computed score).
#
# Deliberately EXCLUDED, with reasons (never "just forgotten"):
#   - Formal scored/computed assessments the clinician calculates themselves,
#     never states as a raw fact to transcribe: performanceStatus.pps/kps/
#     ecog/fast/fastStage, skin.braden.* subscales, skin.pressureInjuryRisk
#     (derived FROM the Braden total), musculoskeletal.adl.* (0-5 ADL scale).
#   - Unbounded free-text fields with no enumerable vocabulary at all (e.g.
#     chestPain.type/frequency, peripheralCirculation, heartSounds,
#     skinColor, catheter sizes/dates) -- these stay in narrative/notes only,
#     never a "concept", per the no-arbitrary-field-path/value rule.
#   - Administrative/workflow checkboxes that are not clinical findings from
#     evidence (shortnessOfBreathScreened, treatmentInitiated/Declined,
#     safetyAssessmentCompleted, fallRiskAssessmentCompleted, etc.) -- these
#     record that a task was DONE by staff, not something evidence reports.
#   - Values like "Other" within an enum/multi list -- not a discrete,
#     verifiable fact a concept can represent.
#
# Where a tri-state/boolean field has a clinically meaningful explicit
# NEGATIVE assertion (e.g. "no edema noted", "lungs clear, no crackles"),
# both the PRESENT and ABSENT concepts are registered -- explicit absence
# reported by a clinician is real information, distinct from the "silently
# missing" case the non-negotiable rules warn against (which is about never
# manufacturing a negative out of the absence of any statement at all).
# ---------------------------------------------------------------------------
CONCEPT_REGISTRY: dict[str, ConceptMapping] = {
    # ═══════════════════════════ PERFORMANCE STATUS ═══════════════════════
    "PERF_NYHA_CLASS_I": ConceptMapping("PERF_NYHA_CLASS_I", "performanceStatus", "NYHA Class I", (_fw("nyha", "I"),)),
    "PERF_NYHA_CLASS_II": ConceptMapping("PERF_NYHA_CLASS_II", "performanceStatus", "NYHA Class II", (_fw("nyha", "II"),)),
    "PERF_NYHA_CLASS_III": ConceptMapping("PERF_NYHA_CLASS_III", "performanceStatus", "NYHA Class III", (_fw("nyha", "III"),)),
    "PERF_NYHA_CLASS_IV": ConceptMapping("PERF_NYHA_CLASS_IV", "performanceStatus", "NYHA Class IV", (_fw("nyha", "IV"),)),

    # ═══════════════════════════ CARDIOVASCULAR ════════════════════════════
    "CV_BP_ORTHOSTATIC": ConceptMapping("CV_BP_ORTHOSTATIC", "cardiovascular", "Orthostatic BP", (_fw("bpSymptoms", "Orthostatic", op="multi_add"),)),
    "CV_BP_HYPERTENSIVE": ConceptMapping("CV_BP_HYPERTENSIVE", "cardiovascular", "Hypertensive", (_fw("bpSymptoms", "Hypertensive", op="multi_add"),)),
    "CV_BP_HYPOTENSIVE": ConceptMapping("CV_BP_HYPOTENSIVE", "cardiovascular", "Hypotensive", (_fw("bpSymptoms", "Hypotensive", op="multi_add"),)),
    "CV_BP_NORMAL": ConceptMapping("CV_BP_NORMAL", "cardiovascular", "BP normal", (_fw("bpSymptoms", "Normal", op="multi_add"),)),
    "CV_PULSE_SITE_APICAL": ConceptMapping("CV_PULSE_SITE_APICAL", "cardiovascular", "Pulse assessed apically", (_fw("pulseSites", "Apical", op="multi_add"),)),
    "CV_PULSE_SITE_PEDAL": ConceptMapping("CV_PULSE_SITE_PEDAL", "cardiovascular", "Pulse assessed pedal", (_fw("pulseSites", "Pedal", op="multi_add"),)),
    "CV_PULSE_SITE_RADIAL": ConceptMapping("CV_PULSE_SITE_RADIAL", "cardiovascular", "Pulse assessed radial", (_fw("pulseSites", "Radial", op="multi_add"),)),
    "CV_PULSE_SITE_FEMORAL": ConceptMapping("CV_PULSE_SITE_FEMORAL", "cardiovascular", "Pulse assessed femoral", (_fw("pulseSites", "Femoral", op="multi_add"),)),
    "CV_PULSE_QUALITY_REGULAR": ConceptMapping("CV_PULSE_QUALITY_REGULAR", "cardiovascular", "Pulse regular", (_fw("pulseQuality", "Regular"),)),
    "CV_PULSE_QUALITY_STRONG": ConceptMapping("CV_PULSE_QUALITY_STRONG", "cardiovascular", "Pulse strong", (_fw("pulseQuality", "Strong"),)),
    "CV_PULSE_QUALITY_WEAK": ConceptMapping("CV_PULSE_QUALITY_WEAK", "cardiovascular", "Pulse weak", (_fw("pulseQuality", "Weak"),)),
    "CV_PULSE_QUALITY_THREADY": ConceptMapping("CV_PULSE_QUALITY_THREADY", "cardiovascular", "Pulse thready", (_fw("pulseQuality", "Thready"),)),
    "CV_PULSE_QUALITY_BOUNDING": ConceptMapping("CV_PULSE_QUALITY_BOUNDING", "cardiovascular", "Pulse bounding", (_fw("pulseQuality", "Bounding"),)),
    "CV_PULSE_QUALITY_IRREGULAR": ConceptMapping("CV_PULSE_QUALITY_IRREGULAR", "cardiovascular", "Pulse irregular", (_fw("pulseQuality", "Irregular"),)),
    "CV_PULSE_QUALITY_TACHYCARDIA": ConceptMapping("CV_PULSE_QUALITY_TACHYCARDIA", "cardiovascular", "Tachycardia", (_fw("pulseQuality", "Tachycardia"),)),
    "CV_PULSE_QUALITY_BRADYCARDIA": ConceptMapping("CV_PULSE_QUALITY_BRADYCARDIA", "cardiovascular", "Bradycardia", (_fw("pulseQuality", "Bradycardia"),)),
    "CV_PULSE_QUALITY_ABSENT": ConceptMapping("CV_PULSE_QUALITY_ABSENT", "cardiovascular", "Pulse absent", (_fw("pulseQuality", "Absent"),)),
    "CV_EDEMA_PRESENT": ConceptMapping("CV_EDEMA_PRESENT", "cardiovascular", "Edema present", (_fw("edema.present", "Yes"),)),
    "CV_EDEMA_ABSENT": ConceptMapping("CV_EDEMA_ABSENT", "cardiovascular", "Edema explicitly absent", (_fw("edema.present", "No"),)),
    "CV_EDEMA_LOC_BILATERAL_LE": ConceptMapping("CV_EDEMA_LOC_BILATERAL_LE", "cardiovascular", "Edema, bilateral LE", (_fw("edema.present", "Yes"), _fw("edema.location", "Bilateral lower extremities", op="multi_add"))),
    "CV_EDEMA_LOC_UNILATERAL_LE": ConceptMapping("CV_EDEMA_LOC_UNILATERAL_LE", "cardiovascular", "Edema, unilateral LE", (_fw("edema.present", "Yes"), _fw("edema.location", "Unilateral LE", op="multi_add"))),
    "CV_EDEMA_LOC_SACRAL": ConceptMapping("CV_EDEMA_LOC_SACRAL", "cardiovascular", "Edema, sacral", (_fw("edema.present", "Yes"), _fw("edema.location", "Sacral", op="multi_add"))),
    "CV_EDEMA_LOC_PERIORBITAL": ConceptMapping("CV_EDEMA_LOC_PERIORBITAL", "cardiovascular", "Edema, periorbital", (_fw("edema.present", "Yes"), _fw("edema.location", "Periorbital", op="multi_add"))),
    "CV_EDEMA_LOC_UPPER_EXTREMITIES": ConceptMapping("CV_EDEMA_LOC_UPPER_EXTREMITIES", "cardiovascular", "Edema, upper extremities", (_fw("edema.present", "Yes"), _fw("edema.location", "Upper extremities", op="multi_add"))),
    "CV_EDEMA_LOC_GENERALIZED": ConceptMapping("CV_EDEMA_LOC_GENERALIZED", "cardiovascular", "Edema, generalized", (_fw("edema.present", "Yes"), _fw("edema.location", "Generalized", op="multi_add"))),
    "CV_EDEMA_SEVERITY_TRACE": ConceptMapping("CV_EDEMA_SEVERITY_TRACE", "cardiovascular", "Edema, trace", (_fw("edema.present", "Yes"), _fw("edema.severity", "Trace"))),
    "CV_EDEMA_SEVERITY_1PLUS": ConceptMapping("CV_EDEMA_SEVERITY_1PLUS", "cardiovascular", "Edema, 1+", (_fw("edema.present", "Yes"), _fw("edema.severity", "1+"))),
    "CV_EDEMA_SEVERITY_2PLUS": ConceptMapping("CV_EDEMA_SEVERITY_2PLUS", "cardiovascular", "Edema, 2+", (_fw("edema.present", "Yes"), _fw("edema.severity", "2+"))),
    "CV_EDEMA_SEVERITY_3PLUS": ConceptMapping("CV_EDEMA_SEVERITY_3PLUS", "cardiovascular", "Edema, 3+", (_fw("edema.present", "Yes"), _fw("edema.severity", "3+"))),
    "CV_EDEMA_SEVERITY_4PLUS": ConceptMapping("CV_EDEMA_SEVERITY_4PLUS", "cardiovascular", "Edema, 4+", (_fw("edema.present", "Yes"), _fw("edema.severity", "4+"))),
    "CV_CHEST_PAIN_PRESENT": ConceptMapping("CV_CHEST_PAIN_PRESENT", "cardiovascular", "Chest pain present", (_fw("chestPain.present", "Yes"),)),
    "CV_CHEST_PAIN_ABSENT": ConceptMapping("CV_CHEST_PAIN_ABSENT", "cardiovascular", "Chest pain explicitly denied", (_fw("chestPain.present", "No"),)),
    "CV_JVD_PRESENT": ConceptMapping("CV_JVD_PRESENT", "cardiovascular", "JVD present", (_fw("jvd", "Yes"),)),
    "CV_JVD_ABSENT": ConceptMapping("CV_JVD_ABSENT", "cardiovascular", "JVD explicitly absent", (_fw("jvd", "No"),)),
    "CV_PACEMAKER_PRESENT": ConceptMapping("CV_PACEMAKER_PRESENT", "cardiovascular", "Pacemaker present", (_fw("pacemaker", True),)),
    "CV_ICD_PRESENT": ConceptMapping("CV_ICD_PRESENT", "cardiovascular", "Internal defibrillator present", (_fw("internalDefibrillator", True),)),
    "CV_VARICOSE_VEINS_PRESENT": ConceptMapping("CV_VARICOSE_VEINS_PRESENT", "cardiovascular", "Varicose veins present", (_fw("varicoseVeins", True),)),
    "CV_CENTRAL_LINE_PRESENT": ConceptMapping("CV_CENTRAL_LINE_PRESENT", "cardiovascular", "Central venous line present", (_fw("centralVenousLine", True),)),
    "CV_COOL_EXTREMITIES_PRESENT": ConceptMapping("CV_COOL_EXTREMITIES_PRESENT", "cardiovascular", "Cool extremities", (_fw("coolExtremities", True),)),
    "CV_COOL_EXTREMITIES_ABSENT": ConceptMapping("CV_COOL_EXTREMITIES_ABSENT", "cardiovascular", "Extremities explicitly warm", (_fw("coolExtremities", False),)),
    "CV_STASIS_ULCER_PRESENT": ConceptMapping("CV_STASIS_ULCER_PRESENT", "cardiovascular", "Stasis ulcer present", (_fw("stasisUlcer", True),)),
    "CV_STASIS_ULCER_ABSENT": ConceptMapping("CV_STASIS_ULCER_ABSENT", "cardiovascular", "Stasis ulcer explicitly absent", (_fw("stasisUlcer", False),)),
    # Objective heart-failure presence/type findings (e.g. "systolic heart
    # failure, chronic", "CHF", "diastolic dysfunction"). Presence is
    # written by every variant so a typed finding (systolic/diastolic)
    # never requires a second separate presence-only finding to also be
    # extracted; type is additive (multi_add) so both can accumulate if
    # documented separately. This does NOT touch hopeComorbidities.heartFailure,
    # which remains auto-derived from the coded Primary/Secondary Diagnosis.
    "CV_HEART_FAILURE_PRESENT": ConceptMapping("CV_HEART_FAILURE_PRESENT", "cardiovascular", "Heart failure present", (_fw("heartFailurePresent", True),)),
    "CV_HEART_FAILURE_SYSTOLIC": ConceptMapping("CV_HEART_FAILURE_SYSTOLIC", "cardiovascular", "Heart failure, systolic", (_fw("heartFailurePresent", True), _fw("heartFailureType", "Systolic", op="multi_add"))),
    "CV_HEART_FAILURE_DIASTOLIC": ConceptMapping("CV_HEART_FAILURE_DIASTOLIC", "cardiovascular", "Heart failure, diastolic", (_fw("heartFailurePresent", True), _fw("heartFailureType", "Diastolic", op="multi_add"))),
    "CV_HEART_FAILURE_UNSPECIFIED_TYPE": ConceptMapping("CV_HEART_FAILURE_UNSPECIFIED_TYPE", "cardiovascular", "Heart failure, unspecified type", (_fw("heartFailurePresent", True), _fw("heartFailureType", "Unspecified", op="multi_add"))),
    "CV_HEART_FAILURE_ABSENT": ConceptMapping("CV_HEART_FAILURE_ABSENT", "cardiovascular", "Heart failure explicitly absent/ruled out", (_fw("heartFailurePresent", False),)),

    # ═══════════════════════════ RESPIRATORY ═══════════════════════════════
    "RESP_SOB_NONE": ConceptMapping("RESP_SOB_NONE", "respiratory", "SOB explicitly denied", (_fw("sobSeverity", "None"),)),
    "RESP_SOB_MILD": ConceptMapping("RESP_SOB_MILD", "respiratory", "SOB mild", (_fw("sobSeverity", "Mild"),)),
    "RESP_SOB_MODERATE": ConceptMapping("RESP_SOB_MODERATE", "respiratory", "SOB moderate", (_fw("sobSeverity", "Moderate"),)),
    "RESP_SOB_SEVERE": ConceptMapping("RESP_SOB_SEVERE", "respiratory", "SOB severe", (_fw("sobSeverity", "Severe"),)),
    "RESP_DYSPNEA_AT_REST": ConceptMapping("RESP_DYSPNEA_AT_REST", "respiratory", "Dyspnea at rest", (_fw("sobSeverity", "At rest"), _fw("exertionLevel", "At rest"))),
    "RESP_DYSPNEA_MINIMAL_EXERTION": ConceptMapping("RESP_DYSPNEA_MINIMAL_EXERTION", "respiratory", "Dyspnea, minimal exertion", (_fw("exertionLevel", "Minimal exertion"),)),
    "RESP_DYSPNEA_MODERATE_EXERTION": ConceptMapping("RESP_DYSPNEA_MODERATE_EXERTION", "respiratory", "Dyspnea, moderate exertion", (_fw("exertionLevel", "Moderate exertion"),)),
    "RESP_DYSPNEA_SEVERE_EXERTION": ConceptMapping("RESP_DYSPNEA_SEVERE_EXERTION", "respiratory", "Dyspnea, severe exertion", (_fw("exertionLevel", "Severe exertion"),)),
    "RESP_DYSPNEA_WITH_SPEECH": ConceptMapping("RESP_DYSPNEA_WITH_SPEECH", "respiratory", "Dyspnea with speech", (_fw("exertionLevel", "With speech"),)),
    "RESP_DYSPNEA_PURSED_LIP_BREATHING": ConceptMapping("RESP_DYSPNEA_PURSED_LIP_BREATHING", "respiratory", "Pursed-lip breathing", (_fw("exertionLevel", "Pursed-lip breathing"),)),
    "RESP_COUGH_PRODUCTIVE": ConceptMapping("RESP_COUGH_PRODUCTIVE", "respiratory", "Productive cough", (_fw("coughType", "Productive"),)),
    "RESP_COUGH_NON_PRODUCTIVE": ConceptMapping("RESP_COUGH_NON_PRODUCTIVE", "respiratory", "Non-productive cough", (_fw("coughType", "Non-productive"),)),
    "RESP_COUGH_HEMOPTYSIS": ConceptMapping("RESP_COUGH_HEMOPTYSIS", "respiratory", "Hemoptysis", (_fw("coughType", "Hemoptysis"),)),
    "RESP_COUGH_NONE": ConceptMapping("RESP_COUGH_NONE", "respiratory", "Cough explicitly denied", (_fw("coughType", "None"),)),
    "RESP_LUNG_SOUNDS_CLEAR": ConceptMapping("RESP_LUNG_SOUNDS_CLEAR", "respiratory", "Lungs clear", (_fw("lungSounds", "Clear", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_CRACKLES": ConceptMapping("RESP_LUNG_SOUNDS_CRACKLES", "respiratory", "Crackles", (_fw("lungSounds", "Crackles", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_WHEEZES": ConceptMapping("RESP_LUNG_SOUNDS_WHEEZES", "respiratory", "Wheezes", (_fw("lungSounds", "Wheezes", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_RHONCHI": ConceptMapping("RESP_LUNG_SOUNDS_RHONCHI", "respiratory", "Rhonchi", (_fw("lungSounds", "Rhonchi", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_DIMINISHED": ConceptMapping("RESP_LUNG_SOUNDS_DIMINISHED", "respiratory", "Diminished breath sounds", (_fw("lungSounds", "Diminished", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_ABSENT": ConceptMapping("RESP_LUNG_SOUNDS_ABSENT", "respiratory", "Absent breath sounds", (_fw("lungSounds", "Absent", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_STRIDOR": ConceptMapping("RESP_LUNG_SOUNDS_STRIDOR", "respiratory", "Stridor", (_fw("lungSounds", "Stridor", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_PLEURAL_RUB": ConceptMapping("RESP_LUNG_SOUNDS_PLEURAL_RUB", "respiratory", "Pleural rub", (_fw("lungSounds", "Pleural rub", op="multi_add"),)),
    "RESP_LUNG_SOUNDS_RALES": ConceptMapping("RESP_LUNG_SOUNDS_RALES", "respiratory", "Rales", (_fw("lungSounds", "Rales", op="multi_add"),)),
    "RESP_PATTERN_REGULAR": ConceptMapping("RESP_PATTERN_REGULAR", "respiratory", "Respirations regular", (_fw("respirations", "Regular", op="multi_add"),)),
    "RESP_PATTERN_IRREGULAR": ConceptMapping("RESP_PATTERN_IRREGULAR", "respiratory", "Respirations irregular", (_fw("respirations", "Irregular", op="multi_add"),)),
    "RESP_PATTERN_LABORED": ConceptMapping("RESP_PATTERN_LABORED", "respiratory", "Labored respirations", (_fw("respirations", "Labored", op="multi_add"),)),
    "RESP_PATTERN_CHEYNE_STOKES": ConceptMapping("RESP_PATTERN_CHEYNE_STOKES", "respiratory", "Cheyne-Stokes respirations", (_fw("respirations", "Cheyne-Stokes", op="multi_add"),)),
    "RESP_PATTERN_APNEIC_EPISODES": ConceptMapping("RESP_PATTERN_APNEIC_EPISODES", "respiratory", "Apneic episodes", (_fw("respirations", "Apneic episodes", op="multi_add"),)),
    "RESP_PATTERN_TACHYPNEA": ConceptMapping("RESP_PATTERN_TACHYPNEA", "respiratory", "Tachypnea", (_fw("respirations", "Tachypnea", op="multi_add"),)),
    "RESP_PATTERN_BRADYPNEA": ConceptMapping("RESP_PATTERN_BRADYPNEA", "respiratory", "Bradypnea", (_fw("respirations", "Bradypnea", op="multi_add"),)),
    "RESP_PATTERN_ORTHOPNEA": ConceptMapping("RESP_PATTERN_ORTHOPNEA", "respiratory", "Orthopnea", (_fw("respirations", "Orthopnea", op="multi_add"),)),
    "RESP_OXYGEN_NOT_IN_USE": ConceptMapping("RESP_OXYGEN_NOT_IN_USE", "respiratory", "Not using supplemental oxygen", (_fw("oxygenTherapy.inUse", False), _fw("oxygenTherapy.onRoomAir", True))),
    "RESP_OXYGEN_NASAL_CANNULA": ConceptMapping(
        "RESP_OXYGEN_NASAL_CANNULA", "respiratory", "Oxygen via nasal cannula",
        (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.type", "Nasal cannula")),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.litersPerMinute", min_value=0, max_value=15),
    ),
    "RESP_OXYGEN_SIMPLE_MASK": ConceptMapping(
        "RESP_OXYGEN_SIMPLE_MASK", "respiratory", "Oxygen via simple mask",
        (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.type", "Simple mask")),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.litersPerMinute", min_value=0, max_value=15),
    ),
    "RESP_OXYGEN_NON_REBREATHER": ConceptMapping(
        "RESP_OXYGEN_NON_REBREATHER", "respiratory", "Oxygen via non-rebreather",
        (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.type", "Non-rebreather")),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.litersPerMinute", min_value=0, max_value=15),
    ),
    "RESP_OXYGEN_VENTURI_MASK": ConceptMapping(
        "RESP_OXYGEN_VENTURI_MASK", "respiratory", "Oxygen via Venturi mask",
        (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.type", "Venturi mask")),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.litersPerMinute", min_value=0, max_value=15),
    ),
    "RESP_OXYGEN_HIGH_FLOW": ConceptMapping(
        "RESP_OXYGEN_HIGH_FLOW", "respiratory", "Oxygen, high flow",
        (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.type", "High flow")),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.litersPerMinute", min_value=0, max_value=60),
    ),
    "RESP_OXYGEN_CONTINUOUS": ConceptMapping("RESP_OXYGEN_CONTINUOUS", "respiratory", "Oxygen delivery continuous", (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.deliveryMode", "Continuous"))),
    "RESP_OXYGEN_PRN": ConceptMapping("RESP_OXYGEN_PRN", "respiratory", "Oxygen delivery PRN", (_fw("oxygenTherapy.inUse", True), _fw("oxygenTherapy.deliveryMode", "PRN"))),
    "RESP_VENTILATOR_SHORT_TERM": ConceptMapping("RESP_VENTILATOR_SHORT_TERM", "respiratory", "Short-term ventilator", (_fw("ventilator.shortTermVentilator", True),)),
    "RESP_VENTILATOR_LONG_TERM": ConceptMapping("RESP_VENTILATOR_LONG_TERM", "respiratory", "Long-term ventilator", (_fw("ventilator.longTermVentilator", True),)),

    # ═══════════════════════════ NEUROLOGICAL ══════════════════════════════
    # motorDeficit/affectedSide/deficitType are new structured fields added
    # specifically to support this concept family (see RNICA.jsx
    # INITIAL_FORM.neurological) -- a real, bounded, closed enum extension,
    # not a freeform field. Each also updates musculoskeletal.paralysis
    # (the mobility/disability classification for the same clinical fact)
    # via a cross-section write, rather than requiring two concepts for one
    # finding.
    "NEURO_HEMIPARESIS_RIGHT": ConceptMapping(
        "NEURO_HEMIPARESIS_RIGHT", "neurological", "Right hemiparesis",
        (_fw("motorDeficit", True), _fw("affectedSide", "Right"), _fw("deficitType", "Hemiparesis", op="multi_add"),
         _fw("paralysis", "Right hemiparesis", section="musculoskeletal")),
    ),
    "NEURO_HEMIPARESIS_LEFT": ConceptMapping(
        "NEURO_HEMIPARESIS_LEFT", "neurological", "Left hemiparesis",
        (_fw("motorDeficit", True), _fw("affectedSide", "Left"), _fw("deficitType", "Hemiparesis", op="multi_add"),
         _fw("paralysis", "Left hemiparesis", section="musculoskeletal")),
    ),
    "NEURO_HEMIPLEGIA_RIGHT": ConceptMapping(
        "NEURO_HEMIPLEGIA_RIGHT", "neurological", "Right hemiplegia",
        (_fw("motorDeficit", True), _fw("affectedSide", "Right"), _fw("deficitType", "Hemiplegia", op="multi_add"),
         _fw("paralysis", "Right hemiplegia", section="musculoskeletal")),
    ),
    "NEURO_HEMIPLEGIA_LEFT": ConceptMapping(
        "NEURO_HEMIPLEGIA_LEFT", "neurological", "Left hemiplegia",
        (_fw("motorDeficit", True), _fw("affectedSide", "Left"), _fw("deficitType", "Hemiplegia", op="multi_add"),
         _fw("paralysis", "Left hemiplegia", section="musculoskeletal")),
    ),
    "NEURO_PARAPLEGIA": ConceptMapping(
        "NEURO_PARAPLEGIA", "neurological", "Paraplegia",
        (_fw("motorDeficit", True), _fw("affectedSide", "Bilateral"), _fw("deficitType", "Plegia", op="multi_add"),
         _fw("paralysis", "Paraplegia", section="musculoskeletal")),
    ),
    "NEURO_QUADRIPLEGIA": ConceptMapping(
        "NEURO_QUADRIPLEGIA", "neurological", "Quadriplegia",
        (_fw("motorDeficit", True), _fw("affectedSide", "Bilateral"), _fw("deficitType", "Plegia", op="multi_add"),
         _fw("paralysis", "Quadriplegia", section="musculoskeletal")),
    ),
    "NEURO_CONSCIOUSNESS_ALERT": ConceptMapping("NEURO_CONSCIOUSNESS_ALERT", "neurological", "Alert", (_fw("consciousness", "Alert"),)),
    "NEURO_CONSCIOUSNESS_LETHARGIC": ConceptMapping("NEURO_CONSCIOUSNESS_LETHARGIC", "neurological", "Lethargic", (_fw("consciousness", "Lethargic"),)),
    "NEURO_CONSCIOUSNESS_OBTUNDED": ConceptMapping("NEURO_CONSCIOUSNESS_OBTUNDED", "neurological", "Obtunded", (_fw("consciousness", "Obtunded"),)),
    "NEURO_CONSCIOUSNESS_STUPOROUS": ConceptMapping("NEURO_CONSCIOUSNESS_STUPOROUS", "neurological", "Stuporous", (_fw("consciousness", "Stuporous"),)),
    "NEURO_CONSCIOUSNESS_COMATOSE": ConceptMapping("NEURO_CONSCIOUSNESS_COMATOSE", "neurological", "Comatose", (_fw("consciousness", "Comatose"),)),
    "NEURO_ORIENTED_TIME": ConceptMapping("NEURO_ORIENTED_TIME", "neurological", "Oriented to time", (_fw("orientation.time", True),)),
    "NEURO_ORIENTED_PLACE": ConceptMapping("NEURO_ORIENTED_PLACE", "neurological", "Oriented to place", (_fw("orientation.place", True),)),
    "NEURO_ORIENTED_PERSON": ConceptMapping("NEURO_ORIENTED_PERSON", "neurological", "Oriented to person", (_fw("orientation.person", True),)),
    "NEURO_ORIENTED_SITUATION": ConceptMapping("NEURO_ORIENTED_SITUATION", "neurological", "Oriented to situation", (_fw("orientation.situation", True),)),
    "NEURO_DISORIENTED": ConceptMapping("NEURO_DISORIENTED", "neurological", "Disoriented", (_fw("orientation.disoriented", True),)),
    "NEURO_COMMUNICATION_CLEAR": ConceptMapping("NEURO_COMMUNICATION_CLEAR", "neurological", "Communication clear", (_fw("communication", "Clear"),)),
    "NEURO_COMMUNICATION_IMPAIRED": ConceptMapping("NEURO_COMMUNICATION_IMPAIRED", "neurological", "Communication impaired", (_fw("communication", "Impaired"),)),
    "NEURO_COMMUNICATION_UNABLE": ConceptMapping("NEURO_COMMUNICATION_UNABLE", "neurological", "Unable to communicate", (_fw("communication", "Unable"),)),
    "NEURO_COMMUNICATION_APHASIA": ConceptMapping("NEURO_COMMUNICATION_APHASIA", "neurological", "Aphasia", (_fw("communication", "Aphasia"),)),
    "NEURO_COMMUNICATION_SLURRED_SPEECH": ConceptMapping("NEURO_COMMUNICATION_SLURRED_SPEECH", "neurological", "Slurred speech", (_fw("communication", "Slurred speech"),)),
    "NEURO_HEARING_ADEQUATE": ConceptMapping("NEURO_HEARING_ADEQUATE", "neurological", "Hearing adequate", (_fw("hearing", "Adequate"),)),
    "NEURO_HEARING_IMPAIRED": ConceptMapping("NEURO_HEARING_IMPAIRED", "neurological", "Hearing impaired", (_fw("hearing", "Impaired"),)),
    "NEURO_HEARING_DEAF": ConceptMapping("NEURO_HEARING_DEAF", "neurological", "Deaf", (_fw("hearing", "Deaf"),)),
    "NEURO_VISION_ADEQUATE": ConceptMapping("NEURO_VISION_ADEQUATE", "neurological", "Vision adequate", (_fw("vision", "Adequate"),)),
    "NEURO_VISION_IMPAIRED": ConceptMapping("NEURO_VISION_IMPAIRED", "neurological", "Vision impaired", (_fw("vision", "Impaired"),)),
    "NEURO_VISION_BLIND": ConceptMapping("NEURO_VISION_BLIND", "neurological", "Blind", (_fw("vision", "Blind"),)),
    "NEURO_BALANCE_STEADY": ConceptMapping("NEURO_BALANCE_STEADY", "neurological", "Balance steady", (_fw("balance", "Steady"),)),
    "NEURO_BALANCE_UNSTEADY": ConceptMapping("NEURO_BALANCE_UNSTEADY", "neurological", "Balance unsteady", (_fw("balance", "Unsteady"),)),
    "NEURO_BALANCE_UNABLE_TO_STAND": ConceptMapping("NEURO_BALANCE_UNABLE_TO_STAND", "neurological", "Unable to stand", (_fw("balance", "Unable to stand"),)),
    "NEURO_SENSORY_NUMBNESS": ConceptMapping("NEURO_SENSORY_NUMBNESS", "neurological", "Numbness", (_fw("sensoryDeficits", "Numbness", op="multi_add"),)),
    "NEURO_SENSORY_TINGLING": ConceptMapping("NEURO_SENSORY_TINGLING", "neurological", "Tingling", (_fw("sensoryDeficits", "Tingling", op="multi_add"),)),
    "NEURO_SENSORY_DECREASED_SENSATION": ConceptMapping("NEURO_SENSORY_DECREASED_SENSATION", "neurological", "Decreased sensation", (_fw("sensoryDeficits", "Decreased sensation", op="multi_add"),)),
    "NEURO_DELIRIUM_PRESENT": ConceptMapping("NEURO_DELIRIUM_PRESENT", "neurological", "Delirium present", (_fw("delirium", True),)),
    "NEURO_SEIZURE_HISTORY": ConceptMapping("NEURO_SEIZURE_HISTORY", "neurological", "Seizure history", (_fw("seizureHistory", True),)),
    "NEURO_DEMEANOR_ANXIETY": ConceptMapping("NEURO_DEMEANOR_ANXIETY", "neurological", "Anxiety", (_fw("symptomsDemeanor", "Anxiety", op="multi_add"),)),
    "NEURO_DEMEANOR_AGITATION": ConceptMapping("NEURO_DEMEANOR_AGITATION", "neurological", "Agitation", (_fw("symptomsDemeanor", "Agitation", op="multi_add"),)),
    "NEURO_DEMEANOR_PEACEFUL": ConceptMapping("NEURO_DEMEANOR_PEACEFUL", "neurological", "Peaceful", (_fw("symptomsDemeanor", "Peaceful", op="multi_add"),)),
    "NEURO_DEMEANOR_CONFUSED": ConceptMapping("NEURO_DEMEANOR_CONFUSED", "neurological", "Confused", (_fw("symptomsDemeanor", "Confused", op="multi_add"),)),
    "NEURO_DEMEANOR_RESTLESS": ConceptMapping("NEURO_DEMEANOR_RESTLESS", "neurological", "Restless", (_fw("symptomsDemeanor", "Restless", op="multi_add"),)),
    "NEURO_DEMEANOR_DEPRESSED": ConceptMapping("NEURO_DEMEANOR_DEPRESSED", "neurological", "Depressed", (_fw("symptomsDemeanor", "Depressed", op="multi_add"),)),
    "NEURO_DEMEANOR_COMBATIVE": ConceptMapping("NEURO_DEMEANOR_COMBATIVE", "neurological", "Combative", (_fw("symptomsDemeanor", "Combative", op="multi_add"),)),

    # ═══════════════════════════ INFECTION ═════════════════════════════════
    # Only CURRENT, explicitly-active infections are ever applied; history
    # (e.g. "resolved sepsis in 2023") is never a CURRENT assertion and is
    # therefore never written to currentInfections -- it only surfaces for
    # clinician review (see note_draft_service.py / ai_extraction_service.py
    # assertion_status handling).
    "INFECT_IMMUNOSUPPRESSED": ConceptMapping("INFECT_IMMUNOSUPPRESSED", "infection", "Immunosuppressed", (_fw("immunosuppressed", True),)),
    "INFECT_ANTIBIOTIC_USE_CURRENT": ConceptMapping("INFECT_ANTIBIOTIC_USE_CURRENT", "infection", "Current antibiotic use", (_fw("antibioticUse", True),)),
    "INFECT_RECURRENT_INFECTION": ConceptMapping("INFECT_RECURRENT_INFECTION", "infection", "Recurrent infection", (_fw("recurrentInfection", True),)),
    "INFECT_PRECAUTIONS_CONTACT": ConceptMapping("INFECT_PRECAUTIONS_CONTACT", "infection", "Contact precautions", (_fw("precautions", "Contact", op="multi_add"),)),
    "INFECT_PRECAUTIONS_DROPLET": ConceptMapping("INFECT_PRECAUTIONS_DROPLET", "infection", "Droplet precautions", (_fw("precautions", "Droplet", op="multi_add"),)),
    "INFECT_PRECAUTIONS_AIRBORNE": ConceptMapping("INFECT_PRECAUTIONS_AIRBORNE", "infection", "Airborne precautions", (_fw("precautions", "Airborne", op="multi_add"),)),
    "INFECT_CURRENT_SEPSIS": ConceptMapping("INFECT_CURRENT_SEPSIS", "infection", "Current sepsis", (_fw("currentInfections", "Sepsis", op="multi_add"),)),
    "INFECT_CURRENT_UTI": ConceptMapping("INFECT_CURRENT_UTI", "infection", "Current UTI", (_fw("currentInfections", "UTI", op="multi_add"),)),
    "INFECT_CURRENT_RESPIRATORY": ConceptMapping("INFECT_CURRENT_RESPIRATORY", "infection", "Current respiratory infection", (_fw("currentInfections", "Respiratory tract", op="multi_add"),)),
    "INFECT_CURRENT_WOUND_INFECTION": ConceptMapping("INFECT_CURRENT_WOUND_INFECTION", "infection", "Current wound infection", (_fw("currentInfections", "Wound", op="multi_add"),)),
    "INFECT_CURRENT_IV_SITE": ConceptMapping("INFECT_CURRENT_IV_SITE", "infection", "Current IV site infection", (_fw("currentInfections", "IV site", op="multi_add"),)),
    "INFECT_CURRENT_PRESSURE_AREA": ConceptMapping("INFECT_CURRENT_PRESSURE_AREA", "infection", "Current pressure area infection", (_fw("currentInfections", "Pressure area", op="multi_add"),)),
    "INFECT_MRSA_CURRENT": ConceptMapping("INFECT_MRSA_CURRENT", "infection", "Current MRSA", (_fw("antibioticResistantInfection", "MRSA", op="multi_add"),)),
    "INFECT_C_DIFF_CURRENT": ConceptMapping("INFECT_C_DIFF_CURRENT", "infection", "Current C. difficile", (_fw("antibioticResistantInfection", "C. difficile", op="multi_add"),)),

    # ═══════════════════════════ SKIN / WOUNDS ═════════════════════════════
    # `location` is the only bounded free-text parameter this module allows
    # anywhere (anatomic sites can't be fully enumerated) -- the draft wound
    # row created is otherwise blank; no stage/size/drainage/treatment is
    # ever invented.
    "SKIN_WOUND_PRESENT": ConceptMapping(
        "SKIN_WOUND_PRESENT", "skin", "Wound present",
        (_fw("skinConditionsPresent", True), _fw("wounds", {}, op="push_draft_row")),
        value_slot=ValueSlot(kind="free_text_bounded", path="wounds[].location", max_len=60),
        draft_row_field="location",
    ),
    "SKIN_STATUS_DRY": ConceptMapping("SKIN_STATUS_DRY", "skin", "Skin dry", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Dry", op="multi_add"))),
    "SKIN_STATUS_FRAGILE": ConceptMapping("SKIN_STATUS_FRAGILE", "skin", "Skin fragile", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Fragile", op="multi_add"))),
    "SKIN_STATUS_EDEMATOUS": ConceptMapping("SKIN_STATUS_EDEMATOUS", "skin", "Skin edematous", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Edematous", op="multi_add"))),
    "SKIN_STATUS_BRUISING": ConceptMapping("SKIN_STATUS_BRUISING", "skin", "Bruising", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Bruising", op="multi_add"))),
    "SKIN_STATUS_RASH": ConceptMapping("SKIN_STATUS_RASH", "skin", "Rash", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Rash", op="multi_add"))),
    "SKIN_STATUS_JAUNDICE": ConceptMapping("SKIN_STATUS_JAUNDICE", "skin", "Jaundice", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Jaundice", op="multi_add"))),
    "SKIN_STATUS_CYANOTIC": ConceptMapping("SKIN_STATUS_CYANOTIC", "skin", "Cyanotic", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Cyanotic", op="multi_add"))),
    "SKIN_STATUS_MOTTLED": ConceptMapping("SKIN_STATUS_MOTTLED", "skin", "Mottled", (_fw("skinConditionsPresent", True), _fw("skinStatus", "Mottled", op="multi_add"))),
    "SKIN_STATUS_INTACT": ConceptMapping("SKIN_STATUS_INTACT", "skin", "Skin intact, no conditions noted", (_fw("skinStatus", "Intact", op="multi_add"),)),
    "SKIN_TURGOR_GOOD": ConceptMapping("SKIN_TURGOR_GOOD", "skin", "Skin turgor good", (_fw("skinTurgor", "Good"),)),
    "SKIN_TURGOR_FAIR": ConceptMapping("SKIN_TURGOR_FAIR", "skin", "Skin turgor fair", (_fw("skinTurgor", "Fair"),)),
    "SKIN_TURGOR_POOR": ConceptMapping("SKIN_TURGOR_POOR", "skin", "Skin turgor poor", (_fw("skinTurgor", "Poor"),)),
    "SKIN_TURGOR_TENTING": ConceptMapping("SKIN_TURGOR_TENTING", "skin", "Skin tenting", (_fw("skinTurgor", "Tenting"),)),

    # ═══════════════════════════ NUTRITION ═════════════════════════════════
    "NUTR_APPETITE_GOOD": ConceptMapping("NUTR_APPETITE_GOOD", "nutrition", "Good appetite", (_fw("appetite", "Good"),)),
    "NUTR_APPETITE_FAIR": ConceptMapping("NUTR_APPETITE_FAIR", "nutrition", "Fair appetite", (_fw("appetite", "Fair"),)),
    "NUTR_APPETITE_POOR": ConceptMapping("NUTR_APPETITE_POOR", "nutrition", "Poor appetite", (_fw("appetite", "Poor"),)),
    "NUTR_APPETITE_ANOREXIC": ConceptMapping("NUTR_APPETITE_ANOREXIC", "nutrition", "Anorexic", (_fw("appetite", "Anorexic"),)),
    "NUTR_FLUID_INTAKE_ADEQUATE": ConceptMapping("NUTR_FLUID_INTAKE_ADEQUATE", "nutrition", "Fluid intake adequate", (_fw("fluidIntake", "Adequate"),)),
    "NUTR_FLUID_INTAKE_DECREASED": ConceptMapping("NUTR_FLUID_INTAKE_DECREASED", "nutrition", "Fluid intake decreased", (_fw("fluidIntake", "Decreased"),)),
    "NUTR_FLUID_INTAKE_MINIMAL": ConceptMapping("NUTR_FLUID_INTAKE_MINIMAL", "nutrition", "Fluid intake minimal", (_fw("fluidIntake", "Minimal"),)),
    "NUTR_DYSPHAGIA": ConceptMapping("NUTR_DYSPHAGIA", "nutrition", "Dysphagia", (_fw("swallowingIssues", "Dysphagia", op="multi_add"),)),
    "NUTR_ASPIRATION_RISK": ConceptMapping("NUTR_ASPIRATION_RISK", "nutrition", "Aspiration risk", (_fw("swallowingIssues", "Aspiration risk", op="multi_add"),)),
    "NUTR_POCKETING": ConceptMapping("NUTR_POCKETING", "nutrition", "Pocketing food", (_fw("swallowingIssues", "Pocketing", op="multi_add"),)),
    "NUTR_COUGHING_WITH_SWALLOWING": ConceptMapping("NUTR_COUGHING_WITH_SWALLOWING", "nutrition", "Coughing with swallowing", (_fw("swallowingIssues", "Coughing with swallowing", op="multi_add"),)),
    "NUTR_NPO": ConceptMapping("NUTR_NPO", "nutrition", "NPO", (_fw("npoStatus", "NPO"),)),
    "NUTR_NPO_EXCEPT_MEDS": ConceptMapping("NUTR_NPO_EXCEPT_MEDS", "nutrition", "NPO except meds", (_fw("npoStatus", "NPO except meds"),)),
    "NUTR_MODIFIED_THICKENED_LIQUIDS": ConceptMapping("NUTR_MODIFIED_THICKENED_LIQUIDS", "nutrition", "Modified/thickened liquids only", (_fw("npoStatus", "Modified/thickened liquids only"),)),
    "NUTR_ARTIFICIAL_FEEDING_PEG": ConceptMapping("NUTR_ARTIFICIAL_FEEDING_PEG", "nutrition", "PEG tube feeding", (_fw("artificialFeeding", "PEG", op="multi_add"),)),
    "NUTR_ARTIFICIAL_FEEDING_NG": ConceptMapping("NUTR_ARTIFICIAL_FEEDING_NG", "nutrition", "NG tube feeding", (_fw("artificialFeeding", "NG", op="multi_add"),)),
    "NUTR_ARTIFICIAL_FEEDING_TPN": ConceptMapping("NUTR_ARTIFICIAL_FEEDING_TPN", "nutrition", "TPN", (_fw("artificialFeeding", "TPN", op="multi_add"),)),
    "NUTR_ORAL_CAVITY_EDENTULOUS": ConceptMapping("NUTR_ORAL_CAVITY_EDENTULOUS", "nutrition", "Edentulous", (_fw("oralCavityFindings", "Edentulous", op="multi_add"),)),
    "NUTR_ORAL_CAVITY_STOMATITIS": ConceptMapping("NUTR_ORAL_CAVITY_STOMATITIS", "nutrition", "Stomatitis", (_fw("oralCavityFindings", "Stomatitis", op="multi_add"),)),
    "NUTR_ORAL_CAVITY_THRUSH": ConceptMapping("NUTR_ORAL_CAVITY_THRUSH", "nutrition", "Thrush", (_fw("oralCavityFindings", "Thrush", op="multi_add"),)),

    # ═══════════════════════════ MUSCULOSKELETAL ═══════════════════════════
    "MSK_WEAKNESS_MILD": ConceptMapping("MSK_WEAKNESS_MILD", "musculoskeletal", "Mild weakness", (_fw("weakness", "Mild"),)),
    "MSK_WEAKNESS_MODERATE": ConceptMapping("MSK_WEAKNESS_MODERATE", "musculoskeletal", "Moderate weakness", (_fw("weakness", "Moderate"),)),
    "MSK_WEAKNESS_SEVERE": ConceptMapping("MSK_WEAKNESS_SEVERE", "musculoskeletal", "Severe weakness", (_fw("weakness", "Severe"),)),
    "MSK_RIGIDITY_PRESENT": ConceptMapping("MSK_RIGIDITY_PRESENT", "musculoskeletal", "Rigidity present", (_fw("rigidityPresent", True),)),
    "MSK_RIGIDITY_SEVERITY_MILD": ConceptMapping("MSK_RIGIDITY_SEVERITY_MILD", "musculoskeletal", "Rigidity, mild", (_fw("rigidityPresent", True), _fw("rigidity", "Mild"))),
    "MSK_RIGIDITY_SEVERITY_MODERATE": ConceptMapping("MSK_RIGIDITY_SEVERITY_MODERATE", "musculoskeletal", "Rigidity, moderate", (_fw("rigidityPresent", True), _fw("rigidity", "Moderate"))),
    "MSK_RIGIDITY_SEVERITY_SEVERE": ConceptMapping("MSK_RIGIDITY_SEVERITY_SEVERE", "musculoskeletal", "Rigidity, severe", (_fw("rigidityPresent", True), _fw("rigidity", "Severe"))),
    "MSK_CONTRACTURES_PRESENT": ConceptMapping("MSK_CONTRACTURES_PRESENT", "musculoskeletal", "Contractures present", (_fw("contracturesPresent", True),)),
    "MSK_CONTRACTURES_SEVERITY_MILD": ConceptMapping("MSK_CONTRACTURES_SEVERITY_MILD", "musculoskeletal", "Contractures, mild", (_fw("contracturesPresent", True), _fw("contractures", "Mild"))),
    "MSK_CONTRACTURES_SEVERITY_MODERATE": ConceptMapping("MSK_CONTRACTURES_SEVERITY_MODERATE", "musculoskeletal", "Contractures, moderate", (_fw("contracturesPresent", True), _fw("contractures", "Moderate"))),
    "MSK_CONTRACTURES_SEVERITY_SEVERE": ConceptMapping("MSK_CONTRACTURES_SEVERITY_SEVERE", "musculoskeletal", "Contractures, severe", (_fw("contracturesPresent", True), _fw("contractures", "Severe"))),
    "MSK_CONTRACTURES_LOC_BILATERAL_LE": ConceptMapping("MSK_CONTRACTURES_LOC_BILATERAL_LE", "musculoskeletal", "Contractures, bilateral LE", (_fw("contracturesLocation", "Bilateral lower extremities", op="multi_add"),)),
    "MSK_CONTRACTURES_LOC_UPPER_EXTREMITIES": ConceptMapping("MSK_CONTRACTURES_LOC_UPPER_EXTREMITIES", "musculoskeletal", "Contractures, upper extremities", (_fw("contracturesLocation", "Upper extremities", op="multi_add"),)),
    "MSK_ROM_LOSS_UPPER_EXTREMITIES": ConceptMapping("MSK_ROM_LOSS_UPPER_EXTREMITIES", "musculoskeletal", "ROM loss, upper extremities", (_fw("romLimitations", "Upper extremities", op="multi_add"),)),
    "MSK_ROM_LOSS_LOWER_EXTREMITIES": ConceptMapping("MSK_ROM_LOSS_LOWER_EXTREMITIES", "musculoskeletal", "ROM loss, lower extremities", (_fw("romLimitations", "Lower extremities", op="multi_add"),)),
    "MSK_ISSUE_JOINT_SWELLING": ConceptMapping("MSK_ISSUE_JOINT_SWELLING", "musculoskeletal", "Joint swelling", (_fw("musculoskeletalIssues", "Joint swelling", op="multi_add"),)),
    "MSK_ISSUE_SPASMS_CRAMPS": ConceptMapping("MSK_ISSUE_SPASMS_CRAMPS", "musculoskeletal", "Spasms / cramps", (_fw("musculoskeletalIssues", "Spasms / cramps", op="multi_add"),)),
    "MSK_ISSUE_AMPUTATION": ConceptMapping("MSK_ISSUE_AMPUTATION", "musculoskeletal", "Amputation", (_fw("musculoskeletalIssues", "Amputation", op="multi_add"),)),
    "MSK_ISSUE_PROSTHESIS": ConceptMapping("MSK_ISSUE_PROSTHESIS", "musculoskeletal", "Prosthesis", (_fw("musculoskeletalIssues", "Prosthesis", op="multi_add"),)),
    "MSK_PARAPLEGIA": ConceptMapping("MSK_PARAPLEGIA", "musculoskeletal", "Paraplegia", (_fw("paralysis", "Paraplegia"),)),
    "MSK_QUADRIPLEGIA": ConceptMapping("MSK_QUADRIPLEGIA", "musculoskeletal", "Quadriplegia", (_fw("paralysis", "Quadriplegia"),)),
    "MSK_GAIT_NORMAL": ConceptMapping("MSK_GAIT_NORMAL", "musculoskeletal", "Gait normal", (_fw("gait", "Normal"),)),
    "MSK_GAIT_UNSTEADY": ConceptMapping("MSK_GAIT_UNSTEADY", "musculoskeletal", "Unsteady gait", (_fw("gait", "Unsteady"),)),
    "MSK_GAIT_SHUFFLING": ConceptMapping("MSK_GAIT_SHUFFLING", "musculoskeletal", "Shuffling gait", (_fw("gait", "Shuffling"),)),
    "MSK_GAIT_UNABLE": ConceptMapping("MSK_GAIT_UNABLE", "musculoskeletal", "Unable to ambulate", (_fw("gait", "Unable"),)),
    "MSK_ASSISTIVE_DEVICE_WALKER": ConceptMapping("MSK_ASSISTIVE_DEVICE_WALKER", "musculoskeletal", "Uses walker", (_fw("assistiveDevices", "Walker", op="multi_add"),)),
    "MSK_ASSISTIVE_DEVICE_WHEELCHAIR": ConceptMapping("MSK_ASSISTIVE_DEVICE_WHEELCHAIR", "musculoskeletal", "Uses wheelchair", (_fw("assistiveDevices", "Wheelchair", op="multi_add"),)),
    "MSK_ASSISTIVE_DEVICE_CANE": ConceptMapping("MSK_ASSISTIVE_DEVICE_CANE", "musculoskeletal", "Uses cane", (_fw("assistiveDevices", "Cane", op="multi_add"),)),
    "MSK_ASSISTIVE_DEVICE_CRUTCHES": ConceptMapping("MSK_ASSISTIVE_DEVICE_CRUTCHES", "musculoskeletal", "Uses crutches", (_fw("assistiveDevices", "Crutches", op="multi_add"),)),
    "MSK_ASSISTIVE_DEVICE_HOSPITAL_BED": ConceptMapping("MSK_ASSISTIVE_DEVICE_HOSPITAL_BED", "musculoskeletal", "Has hospital bed", (_fw("assistiveDevices", "Hospital bed", op="multi_add"),)),
    "MSK_ASSISTIVE_DEVICE_HOYER_LIFT": ConceptMapping("MSK_ASSISTIVE_DEVICE_HOYER_LIFT", "musculoskeletal", "Uses Hoyer lift", (_fw("assistiveDevices", "Hoyer lift", op="multi_add"),)),
    "MSK_AMBULATORY_INDEPENDENT": ConceptMapping("MSK_AMBULATORY_INDEPENDENT", "musculoskeletal", "Ambulatory, independent", (_fw("mobility.ambulatoryStatus", "Independent"),)),
    "MSK_AMBULATORY_SUPERVISED": ConceptMapping("MSK_AMBULATORY_SUPERVISED", "musculoskeletal", "Ambulatory, supervised", (_fw("mobility.ambulatoryStatus", "Supervised"),)),
    "MSK_AMBULATORY_ASSISTED": ConceptMapping("MSK_AMBULATORY_ASSISTED", "musculoskeletal", "Ambulatory, assisted", (_fw("mobility.ambulatoryStatus", "Assisted"),)),
    "MSK_AMBULATORY_DEPENDENT": ConceptMapping("MSK_AMBULATORY_DEPENDENT", "musculoskeletal", "Ambulation dependent", (_fw("mobility.ambulatoryStatus", "Dependent"),)),
    "MSK_BEDBOUND": ConceptMapping("MSK_BEDBOUND", "musculoskeletal", "Bedbound", (_fw("mobility.ambulatoryStatus", "Bedbound"),)),
    "MSK_TRANSFER_INDEPENDENT": ConceptMapping("MSK_TRANSFER_INDEPENDENT", "musculoskeletal", "Transfers independently", (_fw("mobility.transferAbility", "Independent"),)),
    "MSK_TRANSFER_1_PERSON_ASSIST": ConceptMapping("MSK_TRANSFER_1_PERSON_ASSIST", "musculoskeletal", "Transfers, 1-person assist", (_fw("mobility.transferAbility", "1-person assist"),)),
    "MSK_TRANSFER_2_PERSON_ASSIST": ConceptMapping("MSK_TRANSFER_2_PERSON_ASSIST", "musculoskeletal", "Transfers, 2-person assist", (_fw("mobility.transferAbility", "2-person assist"),)),
    "MSK_TRANSFER_HOYER_LIFT": ConceptMapping("MSK_TRANSFER_HOYER_LIFT", "musculoskeletal", "Transfers via Hoyer lift", (_fw("mobility.transferAbility", "Hoyer lift"),)),
    "MSK_STRENGTH_DECREASED": ConceptMapping("MSK_STRENGTH_DECREASED", "musculoskeletal", "Strength decreased", (_fw("strength", "Decreased"),)),
    "MSK_STRENGTH_ABSENT": ConceptMapping("MSK_STRENGTH_ABSENT", "musculoskeletal", "Strength absent", (_fw("strength", "Absent"),)),
    "MSK_BALANCE_IMPAIRED": ConceptMapping("MSK_BALANCE_IMPAIRED", "musculoskeletal", "Balance impaired", (_fw("balance", "Impaired"),)),
    "MSK_PAIN_WITH_MOVEMENT_MILD": ConceptMapping("MSK_PAIN_WITH_MOVEMENT_MILD", "musculoskeletal", "Mild pain with movement", (_fw("painWithMovement", "Mild"),)),
    "MSK_PAIN_WITH_MOVEMENT_MODERATE": ConceptMapping("MSK_PAIN_WITH_MOVEMENT_MODERATE", "musculoskeletal", "Moderate pain with movement", (_fw("painWithMovement", "Moderate"),)),
    "MSK_PAIN_WITH_MOVEMENT_SEVERE": ConceptMapping("MSK_PAIN_WITH_MOVEMENT_SEVERE", "musculoskeletal", "Severe pain with movement", (_fw("painWithMovement", "Severe"),)),
}


def is_known_concept(concept_code: str) -> bool:
    return concept_code in CONCEPT_REGISTRY


def validate_finding(
    raw: Any,
    *,
    source_type: str,
    source_record_id: str | None = None,
    source_date: str | None = None,
    model_version: str | None = None,
    prompt_version: str | None = None,
) -> StructuredFinding | None:
    """Validate one raw model-emitted structured-finding item.

    Returns None (discards) unless ALL of the following hold:
        - concept_code is an exact, recognized key in CONCEPT_REGISTRY
        - source_type is one of the fixed SOURCE_TYPES
        - assertion_status is one of the fixed ASSERTION_STATUSES
        - subject is one of the fixed SUBJECTS (defaults to PATIENT)
        - source_excerpt is present (every finding must be traceable to text)
        - if the concept has a value_slot, the raw "value" satisfies its
          bounds/length; otherwise "value" must be truthy (an asserted fact)

    Never raises.
    """

    try:
        if not isinstance(raw, dict):
            return None

        concept_code = str(raw.get("concept_code") or "").strip()
        mapping = CONCEPT_REGISTRY.get(concept_code)
        if mapping is None:
            return None

        if source_type not in SOURCE_TYPES:
            return None

        assertion_status = str(raw.get("assertion_status") or "").strip().upper()
        if assertion_status not in ASSERTION_STATUSES:
            # No confident assertion classification -- treat as UNCERTAIN
            # rather than silently discarding the whole finding, so it
            # still surfaces for clinician review instead of vanishing.
            assertion_status = "UNCERTAIN"

        subject = str(raw.get("subject") or "PATIENT").strip().upper()
        if subject not in SUBJECTS:
            subject = "PATIENT"

        source_excerpt = str(raw.get("source_excerpt") or "").strip()
        if not source_excerpt:
            return None

        confidence_raw = raw.get("confidence")
        confidence: float | None
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else None
            if confidence is not None:
                confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = None

        value: Any = raw.get("value", True)
        if mapping.value_slot is not None:
            slot = mapping.value_slot
            if slot.kind == "numeric":
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    return None
                if slot.min_value is not None and numeric_value < slot.min_value:
                    return None
                if slot.max_value is not None and numeric_value > slot.max_value:
                    return None
                value = numeric_value
            elif slot.kind == "free_text_bounded":
                text_value = str(value or "").strip()
                if not text_value:
                    return None
                if slot.max_len is not None and len(text_value) > slot.max_len:
                    text_value = text_value[: slot.max_len]
                value = text_value
            else:
                return None
        else:
            # Pure presence concept -- only accept an explicit truthy assertion.
            if value in (False, "false", "False", "0", 0, None, ""):
                return None
            value = True

        return StructuredFinding(
            concept_code=concept_code,
            value=value,
            source_type=source_type,
            source_record_id=source_record_id,
            source_excerpt=source_excerpt[:500],
            source_date=source_date,
            source_location=str(raw.get("source_location") or "").strip() or None,
            confidence=confidence,
            assertion_status=assertion_status,
            subject=subject,
            model_version=model_version,
            prompt_version=prompt_version,
        )
    except Exception:
        return None


# Separates combined multi-site mentions in a free_text_bounded value
# (e.g. "left buttock; right foot", "left buttock and right foot") into
# individual site strings. Deliberately conservative: only splits on
# unambiguous list separators, never on words that could be part of a
# single anatomic description (e.g. does NOT split "right lower leg").
_MULTI_SITE_SEPARATOR_RE = re.compile(r"\s*(?:;|,|\band\b)\s*", re.IGNORECASE)


def split_multi_site_findings(raw_list: Any) -> Any:
    """Defensive backstop for free_text_bounded value slots (e.g. wound
    location): the extraction prompt instructs the model to emit one
    structured_finding per anatomic site, but a model can still combine
    multiple sites into a single string (e.g. "left buttock; right foot").
    When that happens, split that one raw finding dict into N separate
    dicts -- one per site, each otherwise identical (same concept_code,
    source_excerpt, assertion_status, confidence, etc.) -- BEFORE
    validation, so each site becomes its own draft row instead of one
    combined/garbled entry. This runs identically for every source
    pipeline (transcript, H&P/referral, uploaded document, note) so a
    multi-site finding behaves the same regardless of origin.

    No-op for: non-list input, non-dict items, concepts unknown to the
    registry (validate_finding rejects those normally), concepts without a
    free_text_bounded value_slot, or a value that only contains one site.
    """
    if not isinstance(raw_list, list):
        return raw_list
    out: list[Any] = []
    for item in raw_list:
        if not isinstance(item, dict):
            out.append(item)
            continue
        mapping = CONCEPT_REGISTRY.get(item.get("concept_code"))
        value = item.get("value")
        if (
            mapping is not None
            and mapping.value_slot is not None
            and mapping.value_slot.kind == "free_text_bounded"
            and isinstance(value, str)
        ):
            parts = [p.strip() for p in _MULTI_SITE_SEPARATOR_RE.split(value) if p.strip()]
            if len(parts) > 1:
                out.extend({**item, "value": part} for part in parts)
                continue
        out.append(item)
    return out


def validate_findings(
    raw_list: Any,
    *,
    source_type: str,
    source_record_id: str | None = None,
    source_date: str | None = None,
    model_version: str | None = None,
    prompt_version: str | None = None,
) -> list[StructuredFinding]:
    if not isinstance(raw_list, list):
        return []
    out: list[StructuredFinding] = []
    for item in split_multi_site_findings(raw_list):
        parsed = validate_finding(
            item,
            source_type=source_type,
            source_record_id=source_record_id,
            source_date=source_date,
            model_version=model_version,
            prompt_version=prompt_version,
        )
        if parsed is not None:
            out.append(parsed)
    return out


def concept_prompt_catalog() -> str:
    """Render CONCEPT_REGISTRY as compact text for embedding in an LLM
    system prompt -- the model is instructed to only ever emit one of these
    exact concept_code values, never a field_path/value pair directly.
    """

    lines = []
    by_section: dict[str, list[ConceptMapping]] = {}
    for mapping in CONCEPT_REGISTRY.values():
        by_section.setdefault(mapping.section, []).append(mapping)
    for section in sorted(by_section):
        lines.append(f"# {section}")
        for mapping in by_section[section]:
            slot_hint = ""
            if mapping.value_slot is not None:
                if mapping.value_slot.kind == "numeric":
                    slot_hint = " (requires a numeric \"value\", e.g. liters/min)"
                else:
                    slot_hint = " (requires a short \"value\" string, e.g. anatomic location)"
            lines.append(f"  {mapping.concept_code} -- {mapping.label}{slot_hint}")
    return "\n".join(lines)
