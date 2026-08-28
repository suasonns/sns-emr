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

    # ═══════════════════════════ MUSCULOSKELETAL (coverage expansion) ═══
    "ADL_BATHING_INDEPENDENT": ConceptMapping(
        "ADL_BATHING_INDEPENDENT", "musculoskeletal", "Bathing: Independent",
        (_fw("adl.bathing", "0"),),
    ),
    "ADL_BATHING_SETUP_ASSIST_ONLY": ConceptMapping(
        "ADL_BATHING_SETUP_ASSIST_ONLY", "musculoskeletal", "Bathing: Setup assist only",
        (_fw("adl.bathing", "1"),),
    ),
    "ADL_BATHING_SUPERVISION": ConceptMapping(
        "ADL_BATHING_SUPERVISION", "musculoskeletal", "Bathing: Supervision",
        (_fw("adl.bathing", "2"),),
    ),
    "ADL_BATHING_LIMITED_ASSISTANCE": ConceptMapping(
        "ADL_BATHING_LIMITED_ASSISTANCE", "musculoskeletal", "Bathing: Limited assistance",
        (_fw("adl.bathing", "3"),),
    ),
    "ADL_BATHING_EXTENSIVE_ASSISTANCE": ConceptMapping(
        "ADL_BATHING_EXTENSIVE_ASSISTANCE", "musculoskeletal", "Bathing: Extensive assistance",
        (_fw("adl.bathing", "4"),),
    ),
    "ADL_BATHING_TOTAL_DEPENDENCE": ConceptMapping(
        "ADL_BATHING_TOTAL_DEPENDENCE", "musculoskeletal", "Bathing: Total dependence",
        (_fw("adl.bathing", "5"),),
    ),
    "ADL_DRESSING_INDEPENDENT": ConceptMapping(
        "ADL_DRESSING_INDEPENDENT", "musculoskeletal", "Dressing: Independent",
        (_fw("adl.dressing", "0"),),
    ),
    "ADL_DRESSING_SETUP_ASSIST_ONLY": ConceptMapping(
        "ADL_DRESSING_SETUP_ASSIST_ONLY", "musculoskeletal", "Dressing: Setup assist only",
        (_fw("adl.dressing", "1"),),
    ),
    "ADL_DRESSING_SUPERVISION": ConceptMapping(
        "ADL_DRESSING_SUPERVISION", "musculoskeletal", "Dressing: Supervision",
        (_fw("adl.dressing", "2"),),
    ),
    "ADL_DRESSING_LIMITED_ASSISTANCE": ConceptMapping(
        "ADL_DRESSING_LIMITED_ASSISTANCE", "musculoskeletal", "Dressing: Limited assistance",
        (_fw("adl.dressing", "3"),),
    ),
    "ADL_DRESSING_EXTENSIVE_ASSISTANCE": ConceptMapping(
        "ADL_DRESSING_EXTENSIVE_ASSISTANCE", "musculoskeletal", "Dressing: Extensive assistance",
        (_fw("adl.dressing", "4"),),
    ),
    "ADL_DRESSING_TOTAL_DEPENDENCE": ConceptMapping(
        "ADL_DRESSING_TOTAL_DEPENDENCE", "musculoskeletal", "Dressing: Total dependence",
        (_fw("adl.dressing", "5"),),
    ),
    "ADL_TOILETING_INDEPENDENT": ConceptMapping(
        "ADL_TOILETING_INDEPENDENT", "musculoskeletal", "Toileting: Independent",
        (_fw("adl.toileting", "0"),),
    ),
    "ADL_TOILETING_SETUP_ASSIST_ONLY": ConceptMapping(
        "ADL_TOILETING_SETUP_ASSIST_ONLY", "musculoskeletal", "Toileting: Setup assist only",
        (_fw("adl.toileting", "1"),),
    ),
    "ADL_TOILETING_SUPERVISION": ConceptMapping(
        "ADL_TOILETING_SUPERVISION", "musculoskeletal", "Toileting: Supervision",
        (_fw("adl.toileting", "2"),),
    ),
    "ADL_TOILETING_LIMITED_ASSISTANCE": ConceptMapping(
        "ADL_TOILETING_LIMITED_ASSISTANCE", "musculoskeletal", "Toileting: Limited assistance",
        (_fw("adl.toileting", "3"),),
    ),
    "ADL_TOILETING_EXTENSIVE_ASSISTANCE": ConceptMapping(
        "ADL_TOILETING_EXTENSIVE_ASSISTANCE", "musculoskeletal", "Toileting: Extensive assistance",
        (_fw("adl.toileting", "4"),),
    ),
    "ADL_TOILETING_TOTAL_DEPENDENCE": ConceptMapping(
        "ADL_TOILETING_TOTAL_DEPENDENCE", "musculoskeletal", "Toileting: Total dependence",
        (_fw("adl.toileting", "5"),),
    ),
    "ADL_TRANSFERRING_INDEPENDENT": ConceptMapping(
        "ADL_TRANSFERRING_INDEPENDENT", "musculoskeletal", "Transferring: Independent",
        (_fw("adl.transferring", "0"),),
    ),
    "ADL_TRANSFERRING_SETUP_ASSIST_ONLY": ConceptMapping(
        "ADL_TRANSFERRING_SETUP_ASSIST_ONLY", "musculoskeletal", "Transferring: Setup assist only",
        (_fw("adl.transferring", "1"),),
    ),
    "ADL_TRANSFERRING_SUPERVISION": ConceptMapping(
        "ADL_TRANSFERRING_SUPERVISION", "musculoskeletal", "Transferring: Supervision",
        (_fw("adl.transferring", "2"),),
    ),
    "ADL_TRANSFERRING_LIMITED_ASSISTANCE": ConceptMapping(
        "ADL_TRANSFERRING_LIMITED_ASSISTANCE", "musculoskeletal", "Transferring: Limited assistance",
        (_fw("adl.transferring", "3"),),
    ),
    "ADL_TRANSFERRING_EXTENSIVE_ASSISTANCE": ConceptMapping(
        "ADL_TRANSFERRING_EXTENSIVE_ASSISTANCE", "musculoskeletal", "Transferring: Extensive assistance",
        (_fw("adl.transferring", "4"),),
    ),
    "ADL_TRANSFERRING_TOTAL_DEPENDENCE": ConceptMapping(
        "ADL_TRANSFERRING_TOTAL_DEPENDENCE", "musculoskeletal", "Transferring: Total dependence",
        (_fw("adl.transferring", "5"),),
    ),
    "ADL_EATING_INDEPENDENT": ConceptMapping(
        "ADL_EATING_INDEPENDENT", "musculoskeletal", "Eating: Independent",
        (_fw("adl.eating", "0"),),
    ),
    "ADL_EATING_SETUP_ASSIST_ONLY": ConceptMapping(
        "ADL_EATING_SETUP_ASSIST_ONLY", "musculoskeletal", "Eating: Setup assist only",
        (_fw("adl.eating", "1"),),
    ),
    "ADL_EATING_SUPERVISION": ConceptMapping(
        "ADL_EATING_SUPERVISION", "musculoskeletal", "Eating: Supervision",
        (_fw("adl.eating", "2"),),
    ),
    "ADL_EATING_LIMITED_ASSISTANCE": ConceptMapping(
        "ADL_EATING_LIMITED_ASSISTANCE", "musculoskeletal", "Eating: Limited assistance",
        (_fw("adl.eating", "3"),),
    ),
    "ADL_EATING_EXTENSIVE_ASSISTANCE": ConceptMapping(
        "ADL_EATING_EXTENSIVE_ASSISTANCE", "musculoskeletal", "Eating: Extensive assistance",
        (_fw("adl.eating", "4"),),
    ),
    "ADL_EATING_TOTAL_DEPENDENCE": ConceptMapping(
        "ADL_EATING_TOTAL_DEPENDENCE", "musculoskeletal", "Eating: Total dependence",
        (_fw("adl.eating", "5"),),
    ),
    "ADL_GROOMING_INDEPENDENT": ConceptMapping(
        "ADL_GROOMING_INDEPENDENT", "musculoskeletal", "Grooming: Independent",
        (_fw("adl.grooming", "0"),),
    ),
    "ADL_GROOMING_SETUP_ASSIST_ONLY": ConceptMapping(
        "ADL_GROOMING_SETUP_ASSIST_ONLY", "musculoskeletal", "Grooming: Setup assist only",
        (_fw("adl.grooming", "1"),),
    ),
    "ADL_GROOMING_SUPERVISION": ConceptMapping(
        "ADL_GROOMING_SUPERVISION", "musculoskeletal", "Grooming: Supervision",
        (_fw("adl.grooming", "2"),),
    ),
    "ADL_GROOMING_LIMITED_ASSISTANCE": ConceptMapping(
        "ADL_GROOMING_LIMITED_ASSISTANCE", "musculoskeletal", "Grooming: Limited assistance",
        (_fw("adl.grooming", "3"),),
    ),
    "ADL_GROOMING_EXTENSIVE_ASSISTANCE": ConceptMapping(
        "ADL_GROOMING_EXTENSIVE_ASSISTANCE", "musculoskeletal", "Grooming: Extensive assistance",
        (_fw("adl.grooming", "4"),),
    ),
    "ADL_GROOMING_TOTAL_DEPENDENCE": ConceptMapping(
        "ADL_GROOMING_TOTAL_DEPENDENCE", "musculoskeletal", "Grooming: Total dependence",
        (_fw("adl.grooming", "5"),),
    ),
    "MSK_ENDURANCE_GOOD": ConceptMapping(
        "MSK_ENDURANCE_GOOD", "musculoskeletal", "Endurance: good",
        (_fw("mobility.endurance", "Good"),),
    ),
    "MSK_ENDURANCE_FAIR": ConceptMapping(
        "MSK_ENDURANCE_FAIR", "musculoskeletal", "Endurance: fair",
        (_fw("mobility.endurance", "Fair"),),
    ),
    "MSK_ENDURANCE_POOR": ConceptMapping(
        "MSK_ENDURANCE_POOR", "musculoskeletal", "Endurance: poor",
        (_fw("mobility.endurance", "Poor"),),
    ),
    "MSK_FALLS_LAST_90_DAYS": ConceptMapping(
        "MSK_FALLS_LAST_90_DAYS", "musculoskeletal", "Falls in last 90 days",
        (),
        value_slot=ValueSlot(kind="numeric", path="fallHistory.fallsLast90Days", min_value=0, max_value=365),
    ),

    # ═══════════════════════════ GASTROINTESTINAL (coverage expansion) ═══
    "GI_NAUSEA_NONE": ConceptMapping(
        "GI_NAUSEA_NONE", "gastrointestinal", "Nausea, none",
        (_fw("nausea", "None"),),
    ),
    "GI_NAUSEA_MILD": ConceptMapping(
        "GI_NAUSEA_MILD", "gastrointestinal", "Nausea, mild",
        (_fw("nausea", "Mild"),),
    ),
    "GI_NAUSEA_MODERATE": ConceptMapping(
        "GI_NAUSEA_MODERATE", "gastrointestinal", "Nausea, moderate",
        (_fw("nausea", "Moderate"),),
    ),
    "GI_NAUSEA_SEVERE": ConceptMapping(
        "GI_NAUSEA_SEVERE", "gastrointestinal", "Nausea, severe",
        (_fw("nausea", "Severe"),),
    ),
    "GI_VOMITING_NONE": ConceptMapping(
        "GI_VOMITING_NONE", "gastrointestinal", "Vomiting, none",
        (_fw("vomiting", "None"),),
    ),
    "GI_VOMITING_MILD": ConceptMapping(
        "GI_VOMITING_MILD", "gastrointestinal", "Vomiting, mild",
        (_fw("vomiting", "Mild"),),
    ),
    "GI_VOMITING_MODERATE": ConceptMapping(
        "GI_VOMITING_MODERATE", "gastrointestinal", "Vomiting, moderate",
        (_fw("vomiting", "Moderate"),),
    ),
    "GI_VOMITING_SEVERE": ConceptMapping(
        "GI_VOMITING_SEVERE", "gastrointestinal", "Vomiting, severe",
        (_fw("vomiting", "Severe"),),
    ),
    "GI_DIARRHEA_NONE": ConceptMapping(
        "GI_DIARRHEA_NONE", "gastrointestinal", "Diarrhea, none",
        (_fw("diarrhea", "None"),),
    ),
    "GI_DIARRHEA_MILD": ConceptMapping(
        "GI_DIARRHEA_MILD", "gastrointestinal", "Diarrhea, mild",
        (_fw("diarrhea", "Mild"),),
    ),
    "GI_DIARRHEA_MODERATE": ConceptMapping(
        "GI_DIARRHEA_MODERATE", "gastrointestinal", "Diarrhea, moderate",
        (_fw("diarrhea", "Moderate"),),
    ),
    "GI_DIARRHEA_SEVERE": ConceptMapping(
        "GI_DIARRHEA_SEVERE", "gastrointestinal", "Diarrhea, severe",
        (_fw("diarrhea", "Severe"),),
    ),
    "GI_CONSTIPATION_NONE": ConceptMapping(
        "GI_CONSTIPATION_NONE", "gastrointestinal", "Constipation, none",
        (_fw("constipation", "None"),),
    ),
    "GI_CONSTIPATION_MILD": ConceptMapping(
        "GI_CONSTIPATION_MILD", "gastrointestinal", "Constipation, mild",
        (_fw("constipation", "Mild"),),
    ),
    "GI_CONSTIPATION_MODERATE": ConceptMapping(
        "GI_CONSTIPATION_MODERATE", "gastrointestinal", "Constipation, moderate",
        (_fw("constipation", "Moderate"),),
    ),
    "GI_CONSTIPATION_SEVERE": ConceptMapping(
        "GI_CONSTIPATION_SEVERE", "gastrointestinal", "Constipation, severe",
        (_fw("constipation", "Severe"),),
    ),
    "GI_VOMITING_OCCURRENCES_24H": ConceptMapping(
        "GI_VOMITING_OCCURRENCES_24H", "gastrointestinal", "Vomiting occurrences in 24h",
        (),
        value_slot=ValueSlot(kind="numeric", path="vomitingOccurrences24h", min_value=0, max_value=20),
    ),
    "GI_BOWEL_SOUNDS_NORMAL": ConceptMapping(
        "GI_BOWEL_SOUNDS_NORMAL", "gastrointestinal", "Bowel sounds normal",
        (_fw("bowelSounds", "Normal"),),
    ),
    "GI_BOWEL_SOUNDS_HYPERACTIVE": ConceptMapping(
        "GI_BOWEL_SOUNDS_HYPERACTIVE", "gastrointestinal", "Bowel sounds hyperactive",
        (_fw("bowelSounds", "Hyperactive"),),
    ),
    "GI_BOWEL_SOUNDS_HYPOACTIVE": ConceptMapping(
        "GI_BOWEL_SOUNDS_HYPOACTIVE", "gastrointestinal", "Bowel sounds hypoactive",
        (_fw("bowelSounds", "Hypoactive"),),
    ),
    "GI_BOWEL_SOUNDS_ABSENT": ConceptMapping(
        "GI_BOWEL_SOUNDS_ABSENT", "gastrointestinal", "Bowel sounds absent",
        (_fw("bowelSounds", "Absent"),),
    ),
    "GI_ABDOMEN_SOFT": ConceptMapping(
        "GI_ABDOMEN_SOFT", "gastrointestinal", "Abdomen soft",
        (_fw("abdomen", "Soft"),),
    ),
    "GI_ABDOMEN_FIRM": ConceptMapping(
        "GI_ABDOMEN_FIRM", "gastrointestinal", "Abdomen firm",
        (_fw("abdomen", "Firm"),),
    ),
    "GI_ABDOMEN_TYMPANIC": ConceptMapping(
        "GI_ABDOMEN_TYMPANIC", "gastrointestinal", "Abdomen tympanic",
        (_fw("abdomen", "Tympanic"),),
    ),
    "GI_ABDOMEN_DISTENDED": ConceptMapping(
        "GI_ABDOMEN_DISTENDED", "gastrointestinal", "Abdomen distended",
        (_fw("abdomen", "Distended"),),
    ),
    "GI_ABDOMEN_TENDER": ConceptMapping(
        "GI_ABDOMEN_TENDER", "gastrointestinal", "Abdomen tender",
        (_fw("abdomen", "Tender"),),
    ),
    "GI_ABDOMEN_NONTENDER": ConceptMapping(
        "GI_ABDOMEN_NONTENDER", "gastrointestinal", "Abdomen nontender",
        (_fw("abdomen", "Nontender"),),
    ),
    "GI_ABDOMEN_RIGID": ConceptMapping(
        "GI_ABDOMEN_RIGID", "gastrointestinal", "Abdomen rigid",
        (_fw("abdomen", "Rigid"),),
    ),
    "GI_ASCITES_PRESENT": ConceptMapping(
        "GI_ASCITES_PRESENT", "gastrointestinal", "Ascites present",
        (_fw("ascites", True),),
    ),
    "GI_ASCITES_ABSENT": ConceptMapping(
        "GI_ASCITES_ABSENT", "gastrointestinal", "Ascites explicitly absent",
        (_fw("ascites", False),),
    ),
    "GI_STOOL_NORMAL": ConceptMapping(
        "GI_STOOL_NORMAL", "gastrointestinal", "Stool normal",
        (_fw("stoolCharacter", "Normal", op="multi_add"),),
    ),
    "GI_STOOL_BLOODY": ConceptMapping(
        "GI_STOOL_BLOODY", "gastrointestinal", "Stool bloody",
        (_fw("stoolCharacter", "Bloody", op="multi_add"),),
    ),
    "GI_STOOL_COLOSTOMY": ConceptMapping(
        "GI_STOOL_COLOSTOMY", "gastrointestinal", "Stool colostomy",
        (_fw("stoolCharacter", "Colostomy", op="multi_add"),),
    ),
    "GI_STOOL_ILEOSTOMY": ConceptMapping(
        "GI_STOOL_ILEOSTOMY", "gastrointestinal", "Stool ileostomy",
        (_fw("stoolCharacter", "Ileostomy", op="multi_add"),),
    ),
    "GI_BOWEL_STATUS_REGULAR": ConceptMapping(
        "GI_BOWEL_STATUS_REGULAR", "gastrointestinal", "Bowel status: Regular",
        (_fw("bowelStatus", "Regular"),),
    ),
    "GI_BOWEL_STATUS_IRREGULAR": ConceptMapping(
        "GI_BOWEL_STATUS_IRREGULAR", "gastrointestinal", "Bowel status: Irregular",
        (_fw("bowelStatus", "Irregular"),),
    ),
    "GI_BOWEL_STATUS_IMPACTION": ConceptMapping(
        "GI_BOWEL_STATUS_IMPACTION", "gastrointestinal", "Bowel status: Impaction",
        (_fw("bowelStatus", "Impaction"),),
    ),
    "GI_BOWEL_STATUS_CONTINENT": ConceptMapping(
        "GI_BOWEL_STATUS_CONTINENT", "gastrointestinal", "Bowel status: Continent",
        (_fw("bowelStatus", "Continent"),),
    ),
    "GI_BOWEL_STATUS_INCONTINENT": ConceptMapping(
        "GI_BOWEL_STATUS_INCONTINENT", "gastrointestinal", "Bowel status: Incontinent",
        (_fw("bowelStatus", "Incontinent"),),
    ),
    "GI_BOWEL_STATUS_BOWEL_BLADDER_PROGRAM": ConceptMapping(
        "GI_BOWEL_STATUS_BOWEL_BLADDER_PROGRAM", "gastrointestinal", "Bowel status: Bowel/bladder program",
        (_fw("bowelStatus", "Bowel/bladder program"),),
    ),
    "GI_FEEDING_TUBE_PRESENT": ConceptMapping(
        "GI_FEEDING_TUBE_PRESENT", "gastrointestinal", "Feeding tube present",
        (_fw("feedingTube.present", True),),
    ),
    "GI_FEEDING_TUBE_ABSENT": ConceptMapping(
        "GI_FEEDING_TUBE_ABSENT", "gastrointestinal", "Feeding tube explicitly absent",
        (_fw("feedingTube.present", False),),
    ),
    "GI_FEEDING_TUBE_TYPE_NG": ConceptMapping(
        "GI_FEEDING_TUBE_TYPE_NG", "gastrointestinal", "Feeding tube: NG",
        (_fw("feedingTube.present", True), _fw("feedingTube.type", "NG")),
    ),
    "GI_FEEDING_TUBE_TYPE_PEG": ConceptMapping(
        "GI_FEEDING_TUBE_TYPE_PEG", "gastrointestinal", "Feeding tube: PEG",
        (_fw("feedingTube.present", True), _fw("feedingTube.type", "PEG")),
    ),
    "GI_FEEDING_TUBE_TYPE_PEJ": ConceptMapping(
        "GI_FEEDING_TUBE_TYPE_PEJ", "gastrointestinal", "Feeding tube: PEJ",
        (_fw("feedingTube.present", True), _fw("feedingTube.type", "PEJ")),
    ),
    "GI_FEEDING_TUBE_TYPE_G_TUBE": ConceptMapping(
        "GI_FEEDING_TUBE_TYPE_G_TUBE", "gastrointestinal", "Feeding tube: G-tube",
        (_fw("feedingTube.present", True), _fw("feedingTube.type", "G-tube")),
    ),
    "GI_FEEDING_TUBE_TYPE_J_TUBE": ConceptMapping(
        "GI_FEEDING_TUBE_TYPE_J_TUBE", "gastrointestinal", "Feeding tube: J-tube",
        (_fw("feedingTube.present", True), _fw("feedingTube.type", "J-tube")),
    ),
    "GI_OSTOMY_PRESENT": ConceptMapping(
        "GI_OSTOMY_PRESENT", "gastrointestinal", "Ostomy present",
        (_fw("ostomy.present", True),),
    ),
    "GI_OSTOMY_ABSENT": ConceptMapping(
        "GI_OSTOMY_ABSENT", "gastrointestinal", "Ostomy explicitly absent",
        (_fw("ostomy.present", False),),
    ),
    "GI_OSTOMY_TYPE_COLOSTOMY": ConceptMapping(
        "GI_OSTOMY_TYPE_COLOSTOMY", "gastrointestinal", "Ostomy: Colostomy",
        (_fw("ostomy.present", True), _fw("ostomy.type", "Colostomy")),
    ),
    "GI_OSTOMY_TYPE_ILEOSTOMY": ConceptMapping(
        "GI_OSTOMY_TYPE_ILEOSTOMY", "gastrointestinal", "Ostomy: Ileostomy",
        (_fw("ostomy.present", True), _fw("ostomy.type", "Ileostomy")),
    ),
    "GI_OSTOMY_TYPE_UROSTOMY": ConceptMapping(
        "GI_OSTOMY_TYPE_UROSTOMY", "gastrointestinal", "Ostomy: Urostomy",
        (_fw("ostomy.present", True), _fw("ostomy.type", "Urostomy")),
    ),

    # ═══════════════════════════ GENITOURINARY (coverage expansion) ═══
    "GU_URINARY_STATUS_CONTINENT": ConceptMapping(
        "GU_URINARY_STATUS_CONTINENT", "genitourinary", "Urinary status: Continent",
        (_fw("urinaryStatus", "Continent"),),
    ),
    "GU_URINARY_STATUS_STRESS_INCONTINENCE": ConceptMapping(
        "GU_URINARY_STATUS_STRESS_INCONTINENCE", "genitourinary", "Urinary status: Stress incontinence",
        (_fw("urinaryStatus", "Stress incontinence"),),
    ),
    "GU_URINARY_STATUS_URGE_INCONTINENCE": ConceptMapping(
        "GU_URINARY_STATUS_URGE_INCONTINENCE", "genitourinary", "Urinary status: Urge incontinence",
        (_fw("urinaryStatus", "Urge incontinence"),),
    ),
    "GU_URINARY_STATUS_FUNCTIONAL_INCONTINENCE": ConceptMapping(
        "GU_URINARY_STATUS_FUNCTIONAL_INCONTINENCE", "genitourinary", "Urinary status: Functional incontinence",
        (_fw("urinaryStatus", "Functional incontinence"),),
    ),
    "GU_URINARY_STATUS_TOTAL_INCONTINENCE": ConceptMapping(
        "GU_URINARY_STATUS_TOTAL_INCONTINENCE", "genitourinary", "Urinary status: Total incontinence",
        (_fw("urinaryStatus", "Total incontinence"),),
    ),
    "GU_URINARY_STATUS_CATHETERIZED": ConceptMapping(
        "GU_URINARY_STATUS_CATHETERIZED", "genitourinary", "Urinary status: Catheterized",
        (_fw("urinaryStatus", "Catheterized"),),
    ),
    "GU_URINARY_STATUS_BLADDER_PROGRAM": ConceptMapping(
        "GU_URINARY_STATUS_BLADDER_PROGRAM", "genitourinary", "Urinary status: Bladder program",
        (_fw("urinaryStatus", "Bladder program"),),
    ),
    "GU_URINARY_STATUS_UROSTOMY": ConceptMapping(
        "GU_URINARY_STATUS_UROSTOMY", "genitourinary", "Urinary status: Urostomy",
        (_fw("urinaryStatus", "Urostomy"),),
    ),
    "GU_URINARY_STATUS_RETENTION": ConceptMapping(
        "GU_URINARY_STATUS_RETENTION", "genitourinary", "Urinary status: Retention",
        (_fw("urinaryStatus", "Retention"),),
    ),
    "GU_URINARY_STATUS_PAINFUL_URINATION": ConceptMapping(
        "GU_URINARY_STATUS_PAINFUL_URINATION", "genitourinary", "Urinary status: Painful urination",
        (_fw("urinaryStatus", "Painful urination"),),
    ),
    "GU_URINARY_STATUS_NOCTURIA": ConceptMapping(
        "GU_URINARY_STATUS_NOCTURIA", "genitourinary", "Urinary status: Nocturia",
        (_fw("urinaryStatus", "Nocturia"),),
    ),
    "GU_URINE_CHAR_CLEAR": ConceptMapping(
        "GU_URINE_CHAR_CLEAR", "genitourinary", "Urine: clear",
        (_fw("urineCharacteristics", "Clear", op="multi_add"),),
    ),
    "GU_URINE_CHAR_CLOUDY": ConceptMapping(
        "GU_URINE_CHAR_CLOUDY", "genitourinary", "Urine: cloudy",
        (_fw("urineCharacteristics", "Cloudy", op="multi_add"),),
    ),
    "GU_URINE_CHAR_PALE": ConceptMapping(
        "GU_URINE_CHAR_PALE", "genitourinary", "Urine: pale",
        (_fw("urineCharacteristics", "Pale", op="multi_add"),),
    ),
    "GU_URINE_CHAR_BLOOD": ConceptMapping(
        "GU_URINE_CHAR_BLOOD", "genitourinary", "Urine: blood",
        (_fw("urineCharacteristics", "Blood", op="multi_add"),),
    ),
    "GU_URINE_CHAR_ODOR": ConceptMapping(
        "GU_URINE_CHAR_ODOR", "genitourinary", "Urine: odor",
        (_fw("urineCharacteristics", "Odor", op="multi_add"),),
    ),
    "GU_CATHETER_PRESENT": ConceptMapping(
        "GU_CATHETER_PRESENT", "genitourinary", "Catheter present",
        (_fw("catheter.present", True),),
    ),
    "GU_CATHETER_ABSENT": ConceptMapping(
        "GU_CATHETER_ABSENT", "genitourinary", "Catheter explicitly absent",
        (_fw("catheter.present", False),),
    ),
    "GU_CATHETER_TYPE_FOLEY": ConceptMapping(
        "GU_CATHETER_TYPE_FOLEY", "genitourinary", "Catheter: Foley",
        (_fw("catheter.present", True), _fw("catheter.type", "Foley")),
    ),
    "GU_CATHETER_TYPE_SUPRAPUBIC": ConceptMapping(
        "GU_CATHETER_TYPE_SUPRAPUBIC", "genitourinary", "Catheter: Suprapubic",
        (_fw("catheter.present", True), _fw("catheter.type", "Suprapubic")),
    ),
    "GU_CATHETER_TYPE_CONDOM": ConceptMapping(
        "GU_CATHETER_TYPE_CONDOM", "genitourinary", "Catheter: Condom",
        (_fw("catheter.present", True), _fw("catheter.type", "Condom")),
    ),
    "GU_CATHETER_TYPE_INTERMITTENT": ConceptMapping(
        "GU_CATHETER_TYPE_INTERMITTENT", "genitourinary", "Catheter: Intermittent",
        (_fw("catheter.present", True), _fw("catheter.type", "Intermittent")),
    ),
    "GU_CATHETER_TYPE_UROSTOMY": ConceptMapping(
        "GU_CATHETER_TYPE_UROSTOMY", "genitourinary", "Catheter: Urostomy",
        (_fw("catheter.present", True), _fw("catheter.type", "Urostomy")),
    ),
    "GU_CATHETER_CONDITION_PATENT": ConceptMapping(
        "GU_CATHETER_CONDITION_PATENT", "genitourinary", "Catheter condition: patent",
        (_fw("catheter.present", True), _fw("catheter.condition", "Patent")),
    ),
    "GU_CATHETER_CONDITION_BLOCKED": ConceptMapping(
        "GU_CATHETER_CONDITION_BLOCKED", "genitourinary", "Catheter condition: blocked",
        (_fw("catheter.present", True), _fw("catheter.condition", "Blocked")),
    ),
    "GU_CATHETER_CONDITION_LEAKING": ConceptMapping(
        "GU_CATHETER_CONDITION_LEAKING", "genitourinary", "Catheter condition: leaking",
        (_fw("catheter.present", True), _fw("catheter.condition", "Leaking")),
    ),
    "GU_CATHETER_URINE_CLEAR": ConceptMapping(
        "GU_CATHETER_URINE_CLEAR", "genitourinary", "Catheter urine: clear",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Clear", op="multi_add")),
    ),
    "GU_CATHETER_URINE_CLOUDY": ConceptMapping(
        "GU_CATHETER_URINE_CLOUDY", "genitourinary", "Catheter urine: cloudy",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Cloudy", op="multi_add")),
    ),
    "GU_CATHETER_URINE_AMBER": ConceptMapping(
        "GU_CATHETER_URINE_AMBER", "genitourinary", "Catheter urine: amber",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Amber", op="multi_add")),
    ),
    "GU_CATHETER_URINE_DARK": ConceptMapping(
        "GU_CATHETER_URINE_DARK", "genitourinary", "Catheter urine: dark",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Dark", op="multi_add")),
    ),
    "GU_CATHETER_URINE_HEMATURIA": ConceptMapping(
        "GU_CATHETER_URINE_HEMATURIA", "genitourinary", "Catheter urine: hematuria",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Hematuria", op="multi_add")),
    ),
    "GU_CATHETER_URINE_SEDIMENT": ConceptMapping(
        "GU_CATHETER_URINE_SEDIMENT", "genitourinary", "Catheter urine: sediment",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Sediment", op="multi_add")),
    ),
    "GU_CATHETER_URINE_FOUL_ODOR": ConceptMapping(
        "GU_CATHETER_URINE_FOUL_ODOR", "genitourinary", "Catheter urine: foul odor",
        (_fw("catheter.present", True), _fw("catheter.urineCharacteristics", "Foul odor", op="multi_add")),
    ),
    "GU_URINE_OUTPUT_ADEQUATE": ConceptMapping(
        "GU_URINE_OUTPUT_ADEQUATE", "genitourinary", "Urine output: adequate",
        (_fw("urineOutput", "Adequate"),),
    ),
    "GU_URINE_OUTPUT_DECREASED": ConceptMapping(
        "GU_URINE_OUTPUT_DECREASED", "genitourinary", "Urine output: decreased",
        (_fw("urineOutput", "Decreased"),),
    ),
    "GU_URINE_OUTPUT_ANURIA": ConceptMapping(
        "GU_URINE_OUTPUT_ANURIA", "genitourinary", "Urine output: anuria",
        (_fw("urineOutput", "Anuria"),),
    ),
    "GU_URINE_OUTPUT_POLYURIA": ConceptMapping(
        "GU_URINE_OUTPUT_POLYURIA", "genitourinary", "Urine output: polyuria",
        (_fw("urineOutput", "Polyuria"),),
    ),
    "GU_24H_VOLUME": ConceptMapping(
        "GU_24H_VOLUME", "genitourinary", "24-hour urine volume",
        (),
        value_slot=ValueSlot(kind="numeric", path="twentyFourHourVolume", min_value=0, max_value=6000),
    ),
    "GU_REPRO_VAGINAL_BLEEDING": ConceptMapping(
        "GU_REPRO_VAGINAL_BLEEDING", "genitourinary", "Vaginal bleeding",
        (_fw("reproductive.concerns", "Vaginal bleeding", op="multi_add"),),
    ),
    "GU_REPRO_VAGINAL_DISCHARGE": ConceptMapping(
        "GU_REPRO_VAGINAL_DISCHARGE", "genitourinary", "Vaginal discharge",
        (_fw("reproductive.concerns", "Vaginal discharge", op="multi_add"),),
    ),
    "GU_REPRO_PENILE_DISCHARGE": ConceptMapping(
        "GU_REPRO_PENILE_DISCHARGE", "genitourinary", "Penile discharge",
        (_fw("reproductive.concerns", "Penile discharge", op="multi_add"),),
    ),
    "GU_REPRO_SCROTAL_EDEMA": ConceptMapping(
        "GU_REPRO_SCROTAL_EDEMA", "genitourinary", "Scrotal edema",
        (_fw("reproductive.concerns", "Scrotal edema", op="multi_add"),),
    ),
    "GU_REPRO_TESTICULAR_MASS": ConceptMapping(
        "GU_REPRO_TESTICULAR_MASS", "genitourinary", "Testicular mass",
        (_fw("reproductive.concerns", "Testicular mass", op="multi_add"),),
    ),
    "GU_BLADDER_MGMT_BLADDER_TRAINING": ConceptMapping(
        "GU_BLADDER_MGMT_BLADDER_TRAINING", "genitourinary", "Bladder training",
        (_fw("bladderManagement", "Bladder training", op="multi_add"),),
    ),
    "GU_BLADDER_MGMT_SCHEDULED_TOILETING": ConceptMapping(
        "GU_BLADDER_MGMT_SCHEDULED_TOILETING", "genitourinary", "Scheduled toileting",
        (_fw("bladderManagement", "Scheduled toileting", op="multi_add"),),
    ),
    "GU_BLADDER_MGMT_PELVIC_FLOOR_EXERCISES": ConceptMapping(
        "GU_BLADDER_MGMT_PELVIC_FLOOR_EXERCISES", "genitourinary", "Pelvic floor exercises",
        (_fw("bladderManagement", "Pelvic floor exercises", op="multi_add"),),
    ),
    "GU_BLADDER_MGMT_EXTERNAL_COLLECTION_DEVICE": ConceptMapping(
        "GU_BLADDER_MGMT_EXTERNAL_COLLECTION_DEVICE", "genitourinary", "External collection device",
        (_fw("bladderManagement", "External collection device", op="multi_add"),),
    ),

    # ═══════════════════════════ NUTRITION (coverage expansion) ═══
    "NUTR_DENTURES_UPPER": ConceptMapping(
        "NUTR_DENTURES_UPPER", "nutrition", "Upper dentures present",
        (_fw("dentures.upper", True),),
    ),
    "NUTR_DENTURES_LOWER": ConceptMapping(
        "NUTR_DENTURES_LOWER", "nutrition", "Lower dentures present",
        (_fw("dentures.lower", True),),
    ),

    # ═══════════════════════════ SKIN (coverage expansion) ═══
    "SKIN_RELIEF_PRESSURE_RELIEF_MATTRESS": ConceptMapping(
        "SKIN_RELIEF_PRESSURE_RELIEF_MATTRESS", "skin", "Pressure-relief mattress",
        (_fw("pressureReliefMeasures", "Pressure-relief mattress", op="multi_add"),),
    ),
    "SKIN_RELIEF_HEEL_PROTECTORS_FLOATING_HEELS": ConceptMapping(
        "SKIN_RELIEF_HEEL_PROTECTORS_FLOATING_HEELS", "skin", "Heel protectors/floating heels",
        (_fw("pressureReliefMeasures", "Heel protectors/floating heels", op="multi_add"),),
    ),
    "SKIN_RELIEF_CUSHIONED_WHEELCHAIR_SEAT": ConceptMapping(
        "SKIN_RELIEF_CUSHIONED_WHEELCHAIR_SEAT", "skin", "Cushioned wheelchair seat",
        (_fw("pressureReliefMeasures", "Cushioned wheelchair seat", op="multi_add"),),
    ),
    "SKIN_RELIEF_FOAM_GEL_POSITIONING_DEVICES": ConceptMapping(
        "SKIN_RELIEF_FOAM_GEL_POSITIONING_DEVICES", "skin", "Foam/gel positioning devices",
        (_fw("pressureReliefMeasures", "Foam/gel positioning devices", op="multi_add"),),
    ),
    "SKIN_RELIEF_FREQUENT_POSITION_CHANGES": ConceptMapping(
        "SKIN_RELIEF_FREQUENT_POSITION_CHANGES", "skin", "Frequent position changes",
        (_fw("pressureReliefMeasures", "Frequent position changes", op="multi_add"),),
    ),

    # ═══════════════════════════ RESPIRATORY (coverage expansion) ═══
    "RESP_OXYGEN_HOURS_PER_DAY": ConceptMapping(
        "RESP_OXYGEN_HOURS_PER_DAY", "respiratory", "Oxygen hours per day",
        (),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.hoursPerDay", min_value=0, max_value=24),
    ),
    "RESP_SAT_ON_O2": ConceptMapping(
        "RESP_SAT_ON_O2", "respiratory", "SpO2 while on oxygen",
        (),
        value_slot=ValueSlot(kind="numeric", path="oxygenTherapy.satOnO2", min_value=0, max_value=100),
    ),

    # ═══════════════════════════ NEUROLOGICAL (coverage expansion) ═══
    "NEURO_N0500_0": ConceptMapping(
        "NEURO_N0500_0", "neurological", "N0500: None",
        (_fw("hopeItems.n0500", "0"),),
    ),
    "NEURO_N0500_1": ConceptMapping(
        "NEURO_N0500_1", "neurological", "N0500: One word",
        (_fw("hopeItems.n0500", "1"),),
    ),
    "NEURO_N0500_2": ConceptMapping(
        "NEURO_N0500_2", "neurological", "N0500: Two words",
        (_fw("hopeItems.n0500", "2"),),
    ),
    "NEURO_N0500_3": ConceptMapping(
        "NEURO_N0500_3", "neurological", "N0500: Three words",
        (_fw("hopeItems.n0500", "3"),),
    ),
    "NEURO_N0510_0": ConceptMapping(
        "NEURO_N0510_0", "neurological", "N0510: None",
        (_fw("hopeItems.n0510", "0"),),
    ),
    "NEURO_N0510_1": ConceptMapping(
        "NEURO_N0510_1", "neurological", "N0510: One",
        (_fw("hopeItems.n0510", "1"),),
    ),
    "NEURO_N0510_2": ConceptMapping(
        "NEURO_N0510_2", "neurological", "N0510: Two",
        (_fw("hopeItems.n0510", "2"),),
    ),
    "NEURO_N0510_3": ConceptMapping(
        "NEURO_N0510_3", "neurological", "N0510: Three",
        (_fw("hopeItems.n0510", "3"),),
    ),
    "NEURO_N0520_0": ConceptMapping(
        "NEURO_N0520_0", "neurological", "N0520: None correct",
        (_fw("hopeItems.n0520", "0"),),
    ),
    "NEURO_N0520_1": ConceptMapping(
        "NEURO_N0520_1", "neurological", "N0520: Year correct",
        (_fw("hopeItems.n0520", "1"),),
    ),
    "NEURO_N0520_2": ConceptMapping(
        "NEURO_N0520_2", "neurological", "N0520: Month correct",
        (_fw("hopeItems.n0520", "2"),),
    ),
    "NEURO_N0520_3": ConceptMapping(
        "NEURO_N0520_3", "neurological", "N0520: Day of week correct",
        (_fw("hopeItems.n0520", "3"),),
    ),
    "NEURO_SENSORY_AID_GLASSES": ConceptMapping(
        "NEURO_SENSORY_AID_GLASSES", "neurological", "Glasses",
        (_fw("sensoryAids", "Glasses", op="multi_add"),),
    ),
    "NEURO_SENSORY_AID_HEARING_AIDS": ConceptMapping(
        "NEURO_SENSORY_AID_HEARING_AIDS", "neurological", "Hearing aids",
        (_fw("sensoryAids", "Hearing aids", op="multi_add"),),
    ),
    "NEURO_PSYCH_HX_BIPOLAR_DISORDER": ConceptMapping(
        "NEURO_PSYCH_HX_BIPOLAR_DISORDER", "neurological", "Psychiatric history: Bipolar disorder",
        (_fw("psychiatricHistoryType", "Bipolar disorder", op="multi_add"),),
    ),
    "NEURO_PSYCH_HX_OCD": ConceptMapping(
        "NEURO_PSYCH_HX_OCD", "neurological", "Psychiatric history: OCD",
        (_fw("psychiatricHistoryType", "OCD", op="multi_add"),),
    ),
    "NEURO_PSYCH_HX_SCHIZOPHRENIA": ConceptMapping(
        "NEURO_PSYCH_HX_SCHIZOPHRENIA", "neurological", "Psychiatric history: Schizophrenia",
        (_fw("psychiatricHistoryType", "Schizophrenia", op="multi_add"),),
    ),
    "NEURO_PSYCH_HX_DEPRESSION": ConceptMapping(
        "NEURO_PSYCH_HX_DEPRESSION", "neurological", "Psychiatric history: Depression",
        (_fw("psychiatricHistoryType", "Depression", op="multi_add"),),
    ),
    "NEURO_SLEEP_PATTERN_NORMAL": ConceptMapping(
        "NEURO_SLEEP_PATTERN_NORMAL", "neurological", "Sleep pattern: normal",
        (_fw("sleepRest.sleepPattern", "Normal"),),
    ),
    "NEURO_SLEEP_PATTERN_INSOMNIA": ConceptMapping(
        "NEURO_SLEEP_PATTERN_INSOMNIA", "neurological", "Sleep pattern: insomnia",
        (_fw("sleepRest.sleepPattern", "Insomnia"),),
    ),
    "NEURO_SLEEP_PATTERN_HYPERSOMNIA": ConceptMapping(
        "NEURO_SLEEP_PATTERN_HYPERSOMNIA", "neurological", "Sleep pattern: hypersomnia",
        (_fw("sleepRest.sleepPattern", "Hypersomnia"),),
    ),
    "NEURO_SLEEP_PATTERN_FRAGMENTED": ConceptMapping(
        "NEURO_SLEEP_PATTERN_FRAGMENTED", "neurological", "Sleep pattern: fragmented",
        (_fw("sleepRest.sleepPattern", "Fragmented"),),
    ),
    "NEURO_SLEEP_PATTERN_SOMNOLENCE": ConceptMapping(
        "NEURO_SLEEP_PATTERN_SOMNOLENCE", "neurological", "Sleep pattern: somnolence",
        (_fw("sleepRest.sleepPattern", "Somnolence"),),
    ),
    "NEURO_AVG_SLEEP_HOURS": ConceptMapping(
        "NEURO_AVG_SLEEP_HOURS", "neurological", "Average sleep hours",
        (),
        value_slot=ValueSlot(kind="numeric", path="sleepRest.averageSleepHours", min_value=0, max_value=24),
    ),
    "NEURO_NIGHT_SYMPTOM_PAIN": ConceptMapping(
        "NEURO_NIGHT_SYMPTOM_PAIN", "neurological", "Nighttime pain",
        (_fw("sleepRest.nighttimeSymptoms", "Pain", op="multi_add"),),
    ),
    "NEURO_NIGHT_SYMPTOM_DYSPNEA": ConceptMapping(
        "NEURO_NIGHT_SYMPTOM_DYSPNEA", "neurological", "Nighttime dyspnea",
        (_fw("sleepRest.nighttimeSymptoms", "Dyspnea", op="multi_add"),),
    ),
    "NEURO_NIGHT_SYMPTOM_RESTLESSNESS": ConceptMapping(
        "NEURO_NIGHT_SYMPTOM_RESTLESSNESS", "neurological", "Nighttime restlessness",
        (_fw("sleepRest.nighttimeSymptoms", "Restlessness", op="multi_add"),),
    ),
    "NEURO_NIGHT_SYMPTOM_CONFUSION": ConceptMapping(
        "NEURO_NIGHT_SYMPTOM_CONFUSION", "neurological", "Nighttime confusion",
        (_fw("sleepRest.nighttimeSymptoms", "Confusion", op="multi_add"),),
    ),
    "NEURO_NIGHT_SYMPTOM_ANXIETY": ConceptMapping(
        "NEURO_NIGHT_SYMPTOM_ANXIETY", "neurological", "Nighttime anxiety",
        (_fw("sleepRest.nighttimeSymptoms", "Anxiety", op="multi_add"),),
    ),
    "NEURO_NIGHT_SYMPTOM_NAUSEA": ConceptMapping(
        "NEURO_NIGHT_SYMPTOM_NAUSEA", "neurological", "Nighttime nausea",
        (_fw("sleepRest.nighttimeSymptoms", "Nausea", op="multi_add"),),
    ),
    "NEURO_SLEEP_AID_MEDICATION": ConceptMapping(
        "NEURO_SLEEP_AID_MEDICATION", "neurological", "Sleep aid: Medication",
        (_fw("sleepRest.sleepAids", "Medication", op="multi_add"),),
    ),
    "NEURO_SLEEP_AID_POSITIONING": ConceptMapping(
        "NEURO_SLEEP_AID_POSITIONING", "neurological", "Sleep aid: Positioning",
        (_fw("sleepRest.sleepAids", "Positioning", op="multi_add"),),
    ),
    "NEURO_SLEEP_AID_WHITE_NOISE": ConceptMapping(
        "NEURO_SLEEP_AID_WHITE_NOISE", "neurological", "Sleep aid: White noise",
        (_fw("sleepRest.sleepAids", "White noise", op="multi_add"),),
    ),
    "NEURO_SLEEP_AID_WARM_MILK_TEA": ConceptMapping(
        "NEURO_SLEEP_AID_WARM_MILK_TEA", "neurological", "Sleep aid: Warm milk/tea",
        (_fw("sleepRest.sleepAids", "Warm milk/tea", op="multi_add"),),
    ),

    # ═══════════════════════════ VITALS (coverage expansion) ═══════════════
    # Numeric vital signs and IV-access facts routinely stated in H&P/referral
    # vitals lines (e.g. "T 98.6, HR 82, RR 16, BP 128/76, SpO2 96% RA").
    # Deliberately EXCLUDED: bmi (computed from height/weight, never a raw
    # fact), mac/temperatureUnit/heightUnit/weightUnit (unit fields already
    # default to the correct US convention; MAC is essentially never narrated
    # in prose), and every ivAssessment.* logistics field except
    # hasIV/type (size/site/dressingType/insertion+change dates/condition/
    # flushSchedule/notes are line-care documentation, not something an H&P
    # states as a fact to transcribe).
    "VITALS_TEMPERATURE": ConceptMapping(
        "VITALS_TEMPERATURE", "vitals", "Temperature documented",
        (), value_slot=ValueSlot(kind="numeric", path="temperature", min_value=90, max_value=110),
    ),
    "VITALS_PULSE": ConceptMapping(
        "VITALS_PULSE", "vitals", "Pulse documented",
        (), value_slot=ValueSlot(kind="numeric", path="pulse", min_value=20, max_value=220),
    ),
    "VITALS_PULSE_QUALITY_STRONG": ConceptMapping("VITALS_PULSE_QUALITY_STRONG", "vitals", "Pulse strong", (_fw("pulseQuality", "Strong"),)),
    "VITALS_PULSE_QUALITY_WEAK": ConceptMapping("VITALS_PULSE_QUALITY_WEAK", "vitals", "Pulse weak", (_fw("pulseQuality", "Weak"),)),
    "VITALS_PULSE_QUALITY_THREADY": ConceptMapping("VITALS_PULSE_QUALITY_THREADY", "vitals", "Pulse thready", (_fw("pulseQuality", "Thready"),)),
    "VITALS_PULSE_QUALITY_BOUNDING": ConceptMapping("VITALS_PULSE_QUALITY_BOUNDING", "vitals", "Pulse bounding", (_fw("pulseQuality", "Bounding"),)),
    "VITALS_PULSE_QUALITY_IRREGULAR": ConceptMapping("VITALS_PULSE_QUALITY_IRREGULAR", "vitals", "Pulse irregular", (_fw("pulseQuality", "Irregular"),)),
    "VITALS_RESPIRATIONS": ConceptMapping(
        "VITALS_RESPIRATIONS", "vitals", "Respirations documented",
        (), value_slot=ValueSlot(kind="numeric", path="respirations", min_value=4, max_value=60),
    ),
    "VITALS_BP_SYSTOLIC": ConceptMapping(
        "VITALS_BP_SYSTOLIC", "vitals", "BP systolic documented",
        (), value_slot=ValueSlot(kind="numeric", path="bloodPressure.systolic", min_value=40, max_value=260),
    ),
    "VITALS_BP_DIASTOLIC": ConceptMapping(
        "VITALS_BP_DIASTOLIC", "vitals", "BP diastolic documented",
        (), value_slot=ValueSlot(kind="numeric", path="bloodPressure.diastolic", min_value=20, max_value=160),
    ),
    "VITALS_O2_SATURATION": ConceptMapping(
        "VITALS_O2_SATURATION", "vitals", "O2 saturation documented",
        (), value_slot=ValueSlot(kind="numeric", path="oxygenSaturation", min_value=50, max_value=100),
    ),
    "VITALS_O2_SAT_ON_ROOM_AIR": ConceptMapping("VITALS_O2_SAT_ON_ROOM_AIR", "vitals", "SpO2 reading taken on room air", (_fw("oxygenSaturationOnRA", True),)),
    "VITALS_HEIGHT": ConceptMapping(
        "VITALS_HEIGHT", "vitals", "Height documented",
        (), value_slot=ValueSlot(kind="numeric", path="height", min_value=20, max_value=96),
    ),
    "VITALS_WEIGHT": ConceptMapping(
        "VITALS_WEIGHT", "vitals", "Weight documented",
        (), value_slot=ValueSlot(kind="numeric", path="weight", min_value=20, max_value=600),
    ),
    "VITALS_IV_ACCESS_PRESENT": ConceptMapping("VITALS_IV_ACCESS_PRESENT", "vitals", "IV access present", (_fw("ivAssessment.hasIV", True),)),
    "VITALS_IV_TYPE_PERIPHERAL": ConceptMapping("VITALS_IV_TYPE_PERIPHERAL", "vitals", "Peripheral IV", (_fw("ivAssessment.hasIV", True), _fw("ivAssessment.type", "Peripheral"))),
    "VITALS_IV_TYPE_CENTRAL": ConceptMapping("VITALS_IV_TYPE_CENTRAL", "vitals", "Central line", (_fw("ivAssessment.hasIV", True), _fw("ivAssessment.type", "Central"))),
    "VITALS_IV_TYPE_PICC": ConceptMapping("VITALS_IV_TYPE_PICC", "vitals", "PICC line", (_fw("ivAssessment.hasIV", True), _fw("ivAssessment.type", "PICC"))),
    "VITALS_IV_TYPE_PORT": ConceptMapping("VITALS_IV_TYPE_PORT", "vitals", "Port", (_fw("ivAssessment.hasIV", True), _fw("ivAssessment.type", "Port"))),

    # ═══════════════════════════ PAIN (coverage expansion) ══════════════════
    # Deliberately EXCLUDED: flacc.*/painad.* (bedside observation tools the
    # RN scores live during the visit, never a fact stated in a document),
    # comprehensiveAssessmentCompleted/Date and screeningDate (workflow
    # timestamps, not clinical facts), assessmentTool (auto-derived by UI
    # logic from communication status, not evidence), painMapMode (UI toggle),
    # painManagementPlan (RN's own plan, free text).
    "PAIN_SCREENED_YES": ConceptMapping("PAIN_SCREENED_YES", "pain", "Pain screening documented (HOPE J0900.A)", (_fw("screenedForPain", "1"),)),
    "PAIN_SEVERITY_NONE": ConceptMapping("PAIN_SEVERITY_NONE", "pain", "Pain severity: none (HOPE J0900.C)", (_fw("screenedForPain", "1"), _fw("painSeverityCategory", "0"))),
    "PAIN_SEVERITY_MILD": ConceptMapping("PAIN_SEVERITY_MILD", "pain", "Pain severity: mild (HOPE J0900.C)", (_fw("screenedForPain", "1"), _fw("painSeverityCategory", "1"))),
    "PAIN_SEVERITY_MODERATE": ConceptMapping("PAIN_SEVERITY_MODERATE", "pain", "Pain severity: moderate (HOPE J0900.C)", (_fw("screenedForPain", "1"), _fw("painSeverityCategory", "2"))),
    "PAIN_SEVERITY_SEVERE": ConceptMapping("PAIN_SEVERITY_SEVERE", "pain", "Pain severity: severe (HOPE J0900.C)", (_fw("screenedForPain", "1"), _fw("painSeverityCategory", "3"))),
    "PAIN_TOOL_NUMERIC": ConceptMapping("PAIN_TOOL_NUMERIC", "pain", "Pain tool: numeric (HOPE J0900.D)", (_fw("standardizedPainToolType", "1"),)),
    "PAIN_TOOL_VERBAL_DESCRIPTOR": ConceptMapping("PAIN_TOOL_VERBAL_DESCRIPTOR", "pain", "Pain tool: verbal descriptor (HOPE J0900.D)", (_fw("standardizedPainToolType", "2"),)),
    "PAIN_TOOL_PATIENT_VISUAL": ConceptMapping("PAIN_TOOL_PATIENT_VISUAL", "pain", "Pain tool: patient visual (HOPE J0900.D)", (_fw("standardizedPainToolType", "3"),)),
    "PAIN_TOOL_STAFF_OBSERVATION": ConceptMapping("PAIN_TOOL_STAFF_OBSERVATION", "pain", "Pain tool: staff observation (HOPE J0900.D)", (_fw("standardizedPainToolType", "4"),)),
    "PAIN_VERBALIZES_NO": ConceptMapping("PAIN_VERBALIZES_NO", "pain", "Unable/does not verbalize pain", (_fw("verbalizesPain", "0"),)),
    "PAIN_VERBALIZES_RELIABLY": ConceptMapping("PAIN_VERBALIZES_RELIABLY", "pain", "Verbalizes pain reliably", (_fw("verbalizesPain", "1"),)),
    "PAIN_VERBALIZES_SOMETIMES": ConceptMapping("PAIN_VERBALIZES_SOMETIMES", "pain", "Verbalizes pain sometimes", (_fw("verbalizesPain", "2"),)),
    "PAIN_UNCOMFORTABLE_YES": ConceptMapping("PAIN_UNCOMFORTABLE_YES", "pain", "Uncomfortable because of pain", (_fw("uncomfortableBecauseOfPain", "1"),)),
    "PAIN_UNCOMFORTABLE_NO": ConceptMapping("PAIN_UNCOMFORTABLE_NO", "pain", "Not uncomfortable because of pain", (_fw("uncomfortableBecauseOfPain", "0"),)),
    "PAIN_NEUROPATHIC_PRESENT": ConceptMapping("PAIN_NEUROPATHIC_PRESENT", "pain", "Neuropathic pain present (HOPE J0915)", (_fw("neuropathicPain", "1"),)),
    "PAIN_NEUROPATHIC_ABSENT": ConceptMapping("PAIN_NEUROPATHIC_ABSENT", "pain", "Neuropathic pain absent (HOPE J0915)", (_fw("neuropathicPain", "0"),)),
    "PAIN_INTENSITY_CURRENT": ConceptMapping(
        "PAIN_INTENSITY_CURRENT", "pain", "Current pain intensity documented",
        (_fw("screenedForPain", "1"),), value_slot=ValueSlot(kind="numeric", path="painIntensity.current", min_value=0, max_value=10),
    ),
    "PAIN_INTENSITY_WORST": ConceptMapping(
        "PAIN_INTENSITY_WORST", "pain", "Worst pain in 24h documented",
        (), value_slot=ValueSlot(kind="numeric", path="painIntensity.worst", min_value=0, max_value=10),
    ),
    "PAIN_INTENSITY_BEST": ConceptMapping(
        "PAIN_INTENSITY_BEST", "pain", "Best pain in 24h documented",
        (), value_slot=ValueSlot(kind="numeric", path="painIntensity.best", min_value=0, max_value=10),
    ),
    "PAIN_INTENSITY_ACCEPTABLE": ConceptMapping(
        "PAIN_INTENSITY_ACCEPTABLE", "pain", "Acceptable pain level documented",
        (), value_slot=ValueSlot(kind="numeric", path="painIntensity.acceptable", min_value=0, max_value=10),
    ),
    "PAIN_LOCATION_HEAD": ConceptMapping("PAIN_LOCATION_HEAD", "pain", "Pain location: head", (_fw("painLocation", "Head", op="multi_add"),)),
    "PAIN_LOCATION_NECK": ConceptMapping("PAIN_LOCATION_NECK", "pain", "Pain location: neck", (_fw("painLocation", "Neck", op="multi_add"),)),
    "PAIN_LOCATION_CHEST": ConceptMapping("PAIN_LOCATION_CHEST", "pain", "Pain location: chest", (_fw("painLocation", "Chest", op="multi_add"),)),
    "PAIN_LOCATION_ABDOMEN": ConceptMapping("PAIN_LOCATION_ABDOMEN", "pain", "Pain location: abdomen", (_fw("painLocation", "Abdomen", op="multi_add"),)),
    "PAIN_LOCATION_BACK": ConceptMapping("PAIN_LOCATION_BACK", "pain", "Pain location: back", (_fw("painLocation", "Back", op="multi_add"),)),
    "PAIN_LOCATION_UPPER_EXTREMITIES": ConceptMapping("PAIN_LOCATION_UPPER_EXTREMITIES", "pain", "Pain location: upper extremities", (_fw("painLocation", "Upper extremities", op="multi_add"),)),
    "PAIN_LOCATION_LOWER_EXTREMITIES": ConceptMapping("PAIN_LOCATION_LOWER_EXTREMITIES", "pain", "Pain location: lower extremities", (_fw("painLocation", "Lower extremities", op="multi_add"),)),
    "PAIN_LOCATION_GENERALIZED": ConceptMapping("PAIN_LOCATION_GENERALIZED", "pain", "Pain location: generalized", (_fw("painLocation", "Generalized", op="multi_add"),)),
    "PAIN_CHARACTER_SHARP": ConceptMapping("PAIN_CHARACTER_SHARP", "pain", "Pain character: sharp", (_fw("painCharacter", "Sharp", op="multi_add"),)),
    "PAIN_CHARACTER_DULL": ConceptMapping("PAIN_CHARACTER_DULL", "pain", "Pain character: dull", (_fw("painCharacter", "Dull", op="multi_add"),)),
    "PAIN_CHARACTER_ACHING": ConceptMapping("PAIN_CHARACTER_ACHING", "pain", "Pain character: aching", (_fw("painCharacter", "Aching", op="multi_add"),)),
    "PAIN_CHARACTER_BURNING": ConceptMapping("PAIN_CHARACTER_BURNING", "pain", "Pain character: burning", (_fw("painCharacter", "Burning", op="multi_add"),)),
    "PAIN_CHARACTER_STABBING": ConceptMapping("PAIN_CHARACTER_STABBING", "pain", "Pain character: stabbing", (_fw("painCharacter", "Stabbing", op="multi_add"),)),
    "PAIN_CHARACTER_THROBBING": ConceptMapping("PAIN_CHARACTER_THROBBING", "pain", "Pain character: throbbing", (_fw("painCharacter", "Throbbing", op="multi_add"),)),
    "PAIN_CHARACTER_CRAMPING": ConceptMapping("PAIN_CHARACTER_CRAMPING", "pain", "Pain character: cramping", (_fw("painCharacter", "Cramping", op="multi_add"),)),
    "PAIN_CHARACTER_SHOOTING": ConceptMapping("PAIN_CHARACTER_SHOOTING", "pain", "Pain character: shooting", (_fw("painCharacter", "Shooting", op="multi_add"),)),
    "PAIN_CHARACTER_PRESSURE": ConceptMapping("PAIN_CHARACTER_PRESSURE", "pain", "Pain character: pressure", (_fw("painCharacter", "Pressure", op="multi_add"),)),
    "PAIN_AGGRAVATING_MOVEMENT": ConceptMapping("PAIN_AGGRAVATING_MOVEMENT", "pain", "Aggravated by movement", (_fw("aggravatingFactors", "Movement", op="multi_add"),)),
    "PAIN_AGGRAVATING_COUGHING": ConceptMapping("PAIN_AGGRAVATING_COUGHING", "pain", "Aggravated by coughing", (_fw("aggravatingFactors", "Coughing", op="multi_add"),)),
    "PAIN_AGGRAVATING_EATING": ConceptMapping("PAIN_AGGRAVATING_EATING", "pain", "Aggravated by eating", (_fw("aggravatingFactors", "Eating", op="multi_add"),)),
    "PAIN_AGGRAVATING_POSITION_CHANGE": ConceptMapping("PAIN_AGGRAVATING_POSITION_CHANGE", "pain", "Aggravated by position change", (_fw("aggravatingFactors", "Position change", op="multi_add"),)),
    "PAIN_AGGRAVATING_TOUCH": ConceptMapping("PAIN_AGGRAVATING_TOUCH", "pain", "Aggravated by touch", (_fw("aggravatingFactors", "Touch", op="multi_add"),)),
    "PAIN_RELIEVING_MEDICATION": ConceptMapping("PAIN_RELIEVING_MEDICATION", "pain", "Relieved by medication", (_fw("relievingFactors", "Medication", op="multi_add"),)),
    "PAIN_RELIEVING_REST": ConceptMapping("PAIN_RELIEVING_REST", "pain", "Relieved by rest", (_fw("relievingFactors", "Rest", op="multi_add"),)),
    "PAIN_RELIEVING_HEAT": ConceptMapping("PAIN_RELIEVING_HEAT", "pain", "Relieved by heat", (_fw("relievingFactors", "Heat", op="multi_add"),)),
    "PAIN_RELIEVING_COLD": ConceptMapping("PAIN_RELIEVING_COLD", "pain", "Relieved by cold", (_fw("relievingFactors", "Cold", op="multi_add"),)),
    "PAIN_RELIEVING_POSITION_CHANGE": ConceptMapping("PAIN_RELIEVING_POSITION_CHANGE", "pain", "Relieved by position change", (_fw("relievingFactors", "Position change", op="multi_add"),)),
    "PAIN_NONPHARM_REPOSITIONING": ConceptMapping("PAIN_NONPHARM_REPOSITIONING", "pain", "Non-pharm: repositioning", (_fw("nonPharmInterventions", "Repositioning", op="multi_add"),)),
    "PAIN_NONPHARM_HEAT_THERAPY": ConceptMapping("PAIN_NONPHARM_HEAT_THERAPY", "pain", "Non-pharm: heat therapy", (_fw("nonPharmInterventions", "Heat therapy", op="multi_add"),)),
    "PAIN_NONPHARM_COLD_THERAPY": ConceptMapping("PAIN_NONPHARM_COLD_THERAPY", "pain", "Non-pharm: cold therapy", (_fw("nonPharmInterventions", "Cold therapy", op="multi_add"),)),
    "PAIN_NONPHARM_MASSAGE": ConceptMapping("PAIN_NONPHARM_MASSAGE", "pain", "Non-pharm: massage", (_fw("nonPharmInterventions", "Massage", op="multi_add"),)),
    "PAIN_NONPHARM_TENS_UNIT": ConceptMapping("PAIN_NONPHARM_TENS_UNIT", "pain", "Non-pharm: TENS unit", (_fw("nonPharmInterventions", "TENS unit", op="multi_add"),)),

    # ═══════════════════════════ ENDOCRINE (coverage expansion) ═════════════
    # Deliberately EXCLUDED: symptomSeverity (unbounded free-form dict),
    # diabetes.insulinType/insulinDose (unbounded free-text dosing detail --
    # a medication-list concern, not a structured-finding fact), thyroid.notes
    # /notes (free text), diabetes.lastHbA1cDate (workflow date).
    "ENDO_IMPAIRMENT_THYROID": ConceptMapping("ENDO_IMPAIRMENT_THYROID", "endocrine", "Thyroid impairment", (_fw("endocrineImpairment", "Thyroid", op="multi_add"),)),
    "ENDO_IMPAIRMENT_PARATHYROID": ConceptMapping("ENDO_IMPAIRMENT_PARATHYROID", "endocrine", "Parathyroid impairment", (_fw("endocrineImpairment", "Parathyroid", op="multi_add"),)),
    "ENDO_IMPAIRMENT_PITUITARY": ConceptMapping("ENDO_IMPAIRMENT_PITUITARY", "endocrine", "Pituitary impairment", (_fw("endocrineImpairment", "Pituitary", op="multi_add"),)),
    "ENDO_IMPAIRMENT_ADRENAL": ConceptMapping("ENDO_IMPAIRMENT_ADRENAL", "endocrine", "Adrenal impairment", (_fw("endocrineImpairment", "Adrenal", op="multi_add"),)),
    "ENDO_IMPAIRMENT_PANCREAS": ConceptMapping("ENDO_IMPAIRMENT_PANCREAS", "endocrine", "Pancreatic impairment", (_fw("endocrineImpairment", "Pancreas", op="multi_add"),)),
    "ENDO_THYROID_NORMAL": ConceptMapping("ENDO_THYROID_NORMAL", "endocrine", "Thyroid normal", (_fw("thyroid.assessment", "Normal"),)),
    "ENDO_THYROID_ENLARGED": ConceptMapping("ENDO_THYROID_ENLARGED", "endocrine", "Thyroid enlarged", (_fw("thyroid.assessment", "Enlarged"),)),
    "ENDO_THYROID_TENDER": ConceptMapping("ENDO_THYROID_TENDER", "endocrine", "Thyroid tender", (_fw("thyroid.assessment", "Tender"),)),
    "ENDO_THYROID_NODULAR": ConceptMapping("ENDO_THYROID_NODULAR", "endocrine", "Thyroid nodular", (_fw("thyroid.assessment", "Nodular"),)),
    "ENDO_DIABETES_TYPE1": ConceptMapping("ENDO_DIABETES_TYPE1", "endocrine", "Diabetes Type 1", (_fw("diabetes.type", "Type 1"),)),
    "ENDO_DIABETES_TYPE2": ConceptMapping("ENDO_DIABETES_TYPE2", "endocrine", "Diabetes Type 2", (_fw("diabetes.type", "Type 2"),)),
    "ENDO_NOT_DIABETIC": ConceptMapping("ENDO_NOT_DIABETIC", "endocrine", "Not diabetic", (_fw("diabetes.type", "Not diabetic"),)),
    "ENDO_DIABETES_INSULIN_DEPENDENT": ConceptMapping("ENDO_DIABETES_INSULIN_DEPENDENT", "endocrine", "Insulin-dependent diabetes", (_fw("diabetes.dependency", "Insulin-dependent"),)),
    "ENDO_DIABETES_NON_INSULIN_DEPENDENT": ConceptMapping("ENDO_DIABETES_NON_INSULIN_DEPENDENT", "endocrine", "Non-insulin-dependent diabetes", (_fw("diabetes.dependency", "Non-insulin-dependent"),)),
    "ENDO_DIABETES_GLUCOSE_MGMT_CONCERN": ConceptMapping("ENDO_DIABETES_GLUCOSE_MGMT_CONCERN", "endocrine", "Glucose-management concern", (_fw("diabetes.dependency", "Glucose-management concern"),)),
    "ENDO_GLUCOSE_MONITORING_DAILY": ConceptMapping("ENDO_GLUCOSE_MONITORING_DAILY", "endocrine", "Glucose monitoring: daily", (_fw("diabetes.glucoseMonitoring", "Daily"),)),
    "ENDO_GLUCOSE_MONITORING_BID": ConceptMapping("ENDO_GLUCOSE_MONITORING_BID", "endocrine", "Glucose monitoring: BID", (_fw("diabetes.glucoseMonitoring", "BID"),)),
    "ENDO_GLUCOSE_MONITORING_TID": ConceptMapping("ENDO_GLUCOSE_MONITORING_TID", "endocrine", "Glucose monitoring: TID", (_fw("diabetes.glucoseMonitoring", "TID"),)),
    "ENDO_GLUCOSE_MONITORING_QID": ConceptMapping("ENDO_GLUCOSE_MONITORING_QID", "endocrine", "Glucose monitoring: QID", (_fw("diabetes.glucoseMonitoring", "QID"),)),
    "ENDO_GLUCOSE_MONITORING_WEEKLY": ConceptMapping("ENDO_GLUCOSE_MONITORING_WEEKLY", "endocrine", "Glucose monitoring: weekly", (_fw("diabetes.glucoseMonitoring", "Weekly"),)),
    "ENDO_HBA1C_VALUE": ConceptMapping(
        "ENDO_HBA1C_VALUE", "endocrine", "HbA1c value documented",
        (), value_slot=ValueSlot(kind="numeric", path="diabetes.lastHbA1c", min_value=3, max_value=20),
    ),
    "ENDO_ORAL_HYPOGLYCEMIC_METFORMIN": ConceptMapping("ENDO_ORAL_HYPOGLYCEMIC_METFORMIN", "endocrine", "Metformin", (_fw("diabetes.oralHypoglycemics", "Metformin", op="multi_add"),)),
    "ENDO_ORAL_HYPOGLYCEMIC_SULFONYLUREA": ConceptMapping("ENDO_ORAL_HYPOGLYCEMIC_SULFONYLUREA", "endocrine", "Sulfonylurea", (_fw("diabetes.oralHypoglycemics", "Sulfonylurea", op="multi_add"),)),
    "ENDO_ORAL_HYPOGLYCEMIC_DPP4": ConceptMapping("ENDO_ORAL_HYPOGLYCEMIC_DPP4", "endocrine", "DPP-4 inhibitor", (_fw("diabetes.oralHypoglycemics", "DPP-4 inhibitor", op="multi_add"),)),
    "ENDO_ORAL_HYPOGLYCEMIC_SGLT2": ConceptMapping("ENDO_ORAL_HYPOGLYCEMIC_SGLT2", "endocrine", "SGLT2 inhibitor", (_fw("diabetes.oralHypoglycemics", "SGLT2 inhibitor", op="multi_add"),)),
    "ENDO_SYMPTOM_FATIGUE": ConceptMapping("ENDO_SYMPTOM_FATIGUE", "endocrine", "Endocrine fatigue", (_fw("endocrineSymptoms", "Fatigue", op="multi_add"),)),
    "ENDO_SYMPTOM_WEIGHT_CHANGES": ConceptMapping("ENDO_SYMPTOM_WEIGHT_CHANGES", "endocrine", "Weight changes", (_fw("endocrineSymptoms", "Weight changes", op="multi_add"),)),
    "ENDO_SYMPTOM_TEMPERATURE_INTOLERANCE": ConceptMapping("ENDO_SYMPTOM_TEMPERATURE_INTOLERANCE", "endocrine", "Temperature intolerance", (_fw("endocrineSymptoms", "Temperature intolerance", op="multi_add"),)),
    "ENDO_SYMPTOM_HAIR_SKIN_CHANGES": ConceptMapping("ENDO_SYMPTOM_HAIR_SKIN_CHANGES", "endocrine", "Hair/skin changes", (_fw("endocrineSymptoms", "Hair/skin changes", op="multi_add"),)),
    "ENDO_SYMPTOM_POLYDIPSIA": ConceptMapping("ENDO_SYMPTOM_POLYDIPSIA", "endocrine", "Polydipsia", (_fw("endocrineSymptoms", "Polydipsia", op="multi_add"),)),
    "ENDO_SYMPTOM_POLYURIA": ConceptMapping("ENDO_SYMPTOM_POLYURIA", "endocrine", "Polyuria", (_fw("endocrineSymptoms", "Polyuria", op="multi_add"),)),
    "ENDO_SYMPTOM_TREMORS": ConceptMapping("ENDO_SYMPTOM_TREMORS", "endocrine", "Tremors", (_fw("endocrineSymptoms", "Tremors", op="multi_add"),)),
    "ENDO_MED_LEVOTHYROXINE": ConceptMapping("ENDO_MED_LEVOTHYROXINE", "endocrine", "Levothyroxine", (_fw("currentEndocrineMeds", "Levothyroxine", op="multi_add"),)),
    "ENDO_MED_INSULIN": ConceptMapping("ENDO_MED_INSULIN", "endocrine", "Insulin", (_fw("currentEndocrineMeds", "Insulin", op="multi_add"),)),
    "ENDO_MED_ORAL_HYPOGLYCEMICS": ConceptMapping("ENDO_MED_ORAL_HYPOGLYCEMICS", "endocrine", "Oral hypoglycemics", (_fw("currentEndocrineMeds", "Oral hypoglycemics", op="multi_add"),)),
    "ENDO_MED_CORTICOSTEROID_REPLACEMENT": ConceptMapping("ENDO_MED_CORTICOSTEROID_REPLACEMENT", "endocrine", "Corticosteroid replacement", (_fw("currentEndocrineMeds", "Corticosteroid replacement", op="multi_add"),)),

    # ═══════════════════════════ INFECTION / ALLERGIES (coverage expansion) ═
    # `allergies`/`allergyDetails` in INITIAL_FORM are dead formData fields --
    # the rendered Allergies card (AllergiesCard) is backed by its own
    # separate patient-level allergy record/API, not this JSONB blob, so they
    # are intentionally never targeted here (see RNICA.jsx SECTION_CONFIGS.
    # infection -- customRenderer: "patientAllergies").
    "INFECT_HISTORY_MRSA": ConceptMapping("INFECT_HISTORY_MRSA", "infection", "History of MRSA", (_fw("historyOfResistantInfections", "MRSA", op="multi_add"),)),
    "INFECT_HISTORY_C_DIFF": ConceptMapping("INFECT_HISTORY_C_DIFF", "infection", "History of C. difficile", (_fw("historyOfResistantInfections", "C. difficile", op="multi_add"),)),
    "INFECT_TEMPERATURE_DOCUMENTED": ConceptMapping(
        "INFECT_TEMPERATURE_DOCUMENTED", "infection", "Temperature documented (infection context)",
        (), value_slot=ValueSlot(kind="numeric", path="temperature", min_value=90, max_value=110),
    ),

    # ═══════════════════════ GI / NUTRITION / GU (remaining real gaps) ══════
    # `gastrointestinal.continence` and `gastrointestinal.ostomy.condition` are
    # dead INITIAL_FORM fields with no SECTION_CONFIGS entry (only
    # ostomy.present/ostomy.type are rendered) -- intentionally excluded.
    "GI_LAST_BM_DATE": ConceptMapping(
        "GI_LAST_BM_DATE", "gastrointestinal", "Last bowel movement date",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="lastBM", max_len=10),
    ),
    "NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS": ConceptMapping(
        "NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS", "nutrition", "Weight loss (past 6 months)",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="weightLossPastSixMonths", max_len=30),
    ),
    "NUTRITION_DIET_TYPE": ConceptMapping(
        "NUTRITION_DIET_TYPE", "nutrition", "Diet type",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="dietType", max_len=60),
    ),
    "NUTRITION_ORAL_MUCOSA": ConceptMapping(
        "NUTRITION_ORAL_MUCOSA", "nutrition", "Oral mucosa finding",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="oralMucosa", max_len=60),
    ),
    "GU_URINARY_FREQUENCY": ConceptMapping(
        "GU_URINARY_FREQUENCY", "genitourinary", "Urinary frequency",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="frequency", max_len=40),
    ),
    "GU_URINE_COLOR": ConceptMapping(
        "GU_URINE_COLOR", "genitourinary", "Urine color",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="urineColor", max_len=30),
    ),

    # ═══════════════════════ RESPIRATORY (remaining real gaps) ═════════════
    "RESP_SPUTUM_CHARACTER": ConceptMapping(
        "RESP_SPUTUM_CHARACTER", "respiratory", "Sputum character",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="sputumCharacter", max_len=60),
    ),
    "RESP_TRACH_TYPE": ConceptMapping(
        "RESP_TRACH_TYPE", "respiratory", "Tracheostomy type",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="ventilator.tracheostomyType", max_len=40),
    ),
    "RESP_TRACH_SIZE": ConceptMapping(
        "RESP_TRACH_SIZE", "respiratory", "Tracheostomy size",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="ventilator.tracheostomySize", max_len=20),
    ),

    # ═══════════════════════ SKIN (remaining real gap) ═════════════════════
    # `skinBodySites` is a BodyMap of ~90 micro-region IDs (e.g. "left_heel",
    # "sacrum") -- mapping every micro-region is not viable from prose, so
    # only the classic pressure-injury sites that H&P/nursing narrative
    # names explicitly are mapped (the same sites already used as free-text
    # `wounds[].location` values, now also driving the visual body map).
    "SKIN_SITE_SACRUM": ConceptMapping("SKIN_SITE_SACRUM", "skin", "Skin finding at sacrum", (_fw("skinBodySites", "sacrum", op="multi_add"),)),
    "SKIN_SITE_COCCYX": ConceptMapping("SKIN_SITE_COCCYX", "skin", "Skin finding at coccyx", (_fw("skinBodySites", "coccyx", op="multi_add"),)),
    "SKIN_SITE_LEFT_HEEL": ConceptMapping("SKIN_SITE_LEFT_HEEL", "skin", "Skin finding at left heel", (_fw("skinBodySites", "left_heel", op="multi_add"),)),
    "SKIN_SITE_RIGHT_HEEL": ConceptMapping("SKIN_SITE_RIGHT_HEEL", "skin", "Skin finding at right heel", (_fw("skinBodySites", "right_heel", op="multi_add"),)),
    "SKIN_SITE_LEFT_ISCHIAL": ConceptMapping("SKIN_SITE_LEFT_ISCHIAL", "skin", "Skin finding at left ischial tuberosity", (_fw("skinBodySites", "left_ischial", op="multi_add"),)),
    "SKIN_SITE_RIGHT_ISCHIAL": ConceptMapping("SKIN_SITE_RIGHT_ISCHIAL", "skin", "Skin finding at right ischial tuberosity", (_fw("skinBodySites", "right_ischial", op="multi_add"),)),
    "SKIN_SITE_LEFT_TROCHANTER": ConceptMapping("SKIN_SITE_LEFT_TROCHANTER", "skin", "Skin finding at left greater trochanter", (_fw("skinBodySites", "left_trochanter", op="multi_add"),)),
    "SKIN_SITE_RIGHT_TROCHANTER": ConceptMapping("SKIN_SITE_RIGHT_TROCHANTER", "skin", "Skin finding at right greater trochanter", (_fw("skinBodySites", "right_trochanter", op="multi_add"),)),

    # ═══════════════════════ IMMINENT DEATH (real gaps) ═════════════════════
    # `appearsThreeDaysOrLess` (HOPE J0050) is an RN prognosis judgment call,
    # not a fact to auto-populate -- excluded like PPS/KPS/ECOG.
    "IMMINENT_MOTTLING": ConceptMapping("IMMINENT_MOTTLING", "imminentDeath", "Mottling of extremities", (_fw("indicators", "Mottling of extremities", op="multi_add"),)),
    "IMMINENT_MANDIBULAR_BREATHING": ConceptMapping("IMMINENT_MANDIBULAR_BREATHING", "imminentDeath", "Mandibular breathing", (_fw("indicators", "Mandibular breathing", op="multi_add"),)),
    "IMMINENT_APNEIC_PERIODS": ConceptMapping("IMMINENT_APNEIC_PERIODS", "imminentDeath", "Apneic periods", (_fw("indicators", "Apneic periods", op="multi_add"),)),
    "IMMINENT_CYANOSIS": ConceptMapping("IMMINENT_CYANOSIS", "imminentDeath", "Cyanosis", (_fw("indicators", "Cyanosis", op="multi_add"),)),
    "IMMINENT_NO_URINE_OUTPUT": ConceptMapping("IMMINENT_NO_URINE_OUTPUT", "imminentDeath", "No urine output", (_fw("indicators", "No urine output", op="multi_add"),)),
    "IMMINENT_UNRESPONSIVE": ConceptMapping("IMMINENT_UNRESPONSIVE", "imminentDeath", "Unresponsive", (_fw("indicators", "Unresponsive", op="multi_add"),)),
    "IMMINENT_DEATH_RATTLE": ConceptMapping("IMMINENT_DEATH_RATTLE", "imminentDeath", "Death rattle", (_fw("indicators", "Death rattle", op="multi_add"),)),
    "IMMINENT_CHEYNE_STOKES": ConceptMapping("IMMINENT_CHEYNE_STOKES", "imminentDeath", "Cheyne-Stokes breathing", (_fw("indicators", "Cheyne-Stokes breathing", op="multi_add"),)),
    "IMMINENT_COOL_COLD_EXTREMITIES": ConceptMapping("IMMINENT_COOL_COLD_EXTREMITIES", "imminentDeath", "Cool/cold extremities", (_fw("indicators", "Cool/cold extremities", op="multi_add"),)),
    "IMMINENT_DECREASED_LOC": ConceptMapping("IMMINENT_DECREASED_LOC", "imminentDeath", "Decreased level of consciousness", (_fw("indicators", "Decreased level of consciousness", op="multi_add"),)),
    "IMMINENT_INABILITY_TO_SWALLOW": ConceptMapping("IMMINENT_INABILITY_TO_SWALLOW", "imminentDeath", "Inability to swallow", (_fw("indicators", "Inability to swallow", op="multi_add"),)),
    "IMMINENT_COMFORT_MEASURES_IN_PLACE": ConceptMapping("IMMINENT_COMFORT_MEASURES_IN_PLACE", "imminentDeath", "Comfort measures in place", (_fw("comfortMeasuresInPlace", True),)),
    "IMMINENT_FAMILY_NOTIFIED": ConceptMapping("IMMINENT_FAMILY_NOTIFIED", "imminentDeath", "Family notified", (_fw("familyNotified", True),)),

    # ═══════════════════════ SAFETY (real gaps) ═════════════════════════════
    # `safetyAssessmentCompleted`/`fallRiskAssessmentCompleted`/
    # `oxygenSafetyReviewed`/`incidentOccurrenceReported(+Notes)` are
    # workflow-completion attestations for THIS visit, not admission facts --
    # excluded per the RN-owned workflow-action rule. `disasterLevel` and its
    # three condition checklists are a computed CMS triage classification
    # (protocol-derived, not a source-document fact) -- excluded; `supplies.*`
    # and the DME custom renderer are plan/order items, not extraction scope.
    "SAFETY_HOME_ADEQUATE_LIGHTING": ConceptMapping("SAFETY_HOME_ADEQUATE_LIGHTING", "safety", "Adequate lighting", (_fw("homeEnvironment", "Adequate lighting", op="multi_add"),)),
    "SAFETY_HOME_HANDRAILS": ConceptMapping("SAFETY_HOME_HANDRAILS", "safety", "Handrails present", (_fw("homeEnvironment", "Handrails present", op="multi_add"),)),
    "SAFETY_HOME_THROW_RUGS": ConceptMapping("SAFETY_HOME_THROW_RUGS", "safety", "Throw rugs", (_fw("homeEnvironment", "Throw rugs", op="multi_add"),)),
    "SAFETY_HOME_CLUTTER": ConceptMapping("SAFETY_HOME_CLUTTER", "safety", "Clutter/obstacles", (_fw("homeEnvironment", "Clutter/obstacles", op="multi_add"),)),
    "SAFETY_HOME_STAIRS_NO_RAILING": ConceptMapping("SAFETY_HOME_STAIRS_NO_RAILING", "safety", "Stairs without railing", (_fw("homeEnvironment", "Stairs without railing", op="multi_add"),)),
    "SAFETY_HOME_PETS": ConceptMapping("SAFETY_HOME_PETS", "safety", "Pets", (_fw("homeEnvironment", "Pets", op="multi_add"),)),
    "SAFETY_HOME_WEAPONS_FIREARMS": ConceptMapping("SAFETY_HOME_WEAPONS_FIREARMS", "safety", "Weapons/firearms", (_fw("homeEnvironment", "Weapons/firearms", op="multi_add"), _fw("firearmInHome", True))),
    "SAFETY_HOME_PEST_INFESTATION": ConceptMapping("SAFETY_HOME_PEST_INFESTATION", "safety", "Pest infestation", (_fw("homeEnvironment", "Pest infestation", op="multi_add"),)),
    "SAFETY_HOME_INADEQUATE_HEATING_COOLING": ConceptMapping("SAFETY_HOME_INADEQUATE_HEATING_COOLING", "safety", "Inadequate heating/cooling", (_fw("homeEnvironment", "Inadequate heating/cooling", op="multi_add"),)),
    "SAFETY_HOME_SMOKE_DETECTORS": ConceptMapping("SAFETY_HOME_SMOKE_DETECTORS", "safety", "Smoke detectors present", (_fw("homeEnvironment", "Smoke detectors present", op="multi_add"),)),
    "SAFETY_FALL_RISK_LOW": ConceptMapping("SAFETY_FALL_RISK_LOW", "safety", "Fall risk documented as low", (_fw("fallRiskLevel", "Low"),)),
    "SAFETY_FALL_RISK_MODERATE": ConceptMapping("SAFETY_FALL_RISK_MODERATE", "safety", "Fall risk documented as moderate", (_fw("fallRiskLevel", "Moderate"),)),
    "SAFETY_FALL_RISK_HIGH": ConceptMapping("SAFETY_FALL_RISK_HIGH", "safety", "Fall risk documented as high", (_fw("fallRiskLevel", "High"),)),
    "SAFETY_TRANSFER_INDEPENDENT": ConceptMapping("SAFETY_TRANSFER_INDEPENDENT", "safety", "Transfers independently", (_fw("transferSafetyLevel", "Independent"),)),
    "SAFETY_TRANSFER_ASSIST_X1": ConceptMapping("SAFETY_TRANSFER_ASSIST_X1", "safety", "Transfers with assist x1", (_fw("transferSafetyLevel", "Needs assist x1"),)),
    "SAFETY_TRANSFER_ASSIST_X2": ConceptMapping("SAFETY_TRANSFER_ASSIST_X2", "safety", "Transfers with assist x2", (_fw("transferSafetyLevel", "Needs assist x2"),)),
    "SAFETY_TRANSFER_MECHANICAL_LIFT": ConceptMapping("SAFETY_TRANSFER_MECHANICAL_LIFT", "safety", "Requires mechanical lift for transfer", (_fw("transferSafetyLevel", "Mechanical lift required"),)),
    "SAFETY_TRANSFER_UNSAFE": ConceptMapping("SAFETY_TRANSFER_UNSAFE", "safety", "Transfers documented as unsafe/high risk", (_fw("transferSafetyLevel", "Unsafe/high risk"),)),
    "SAFETY_OXYGEN_IN_USE": ConceptMapping("SAFETY_OXYGEN_IN_USE", "safety", "Oxygen in use", (_fw("oxygenInUse", True),)),

    # ═══════════════════════ PSYCHOSOCIAL (real gaps) ═══════════════════════
    # `copingAssessment` (Effective/Developing/Ineffective/Crisis) is an
    # RN/MSW clinical judgment call, not a fact -- excluded. `interventionPlan`
    # and `socialWorkVisitNeeded` are plan/referral decisions the discipline
    # makes, not facts present in admission documents -- excluded.
    "PSYCH_SUPPORT_STRONG": ConceptMapping("PSYCH_SUPPORT_STRONG", "psychosocial", "Strong family/social support", (_fw("familySocialSupport", "Strong support"),)),
    "PSYCH_SUPPORT_ADEQUATE": ConceptMapping("PSYCH_SUPPORT_ADEQUATE", "psychosocial", "Adequate family/social support", (_fw("familySocialSupport", "Adequate support"),)),
    "PSYCH_SUPPORT_LIMITED": ConceptMapping("PSYCH_SUPPORT_LIMITED", "psychosocial", "Limited family/social support", (_fw("familySocialSupport", "Limited support"),)),
    "PSYCH_SUPPORT_NONE": ConceptMapping("PSYCH_SUPPORT_NONE", "psychosocial", "No family/social support", (_fw("familySocialSupport", "No support"),)),
    "PSYCH_PRIMARY_SUPPORT_PERSON": ConceptMapping(
        "PSYCH_PRIMARY_SUPPORT_PERSON", "psychosocial", "Primary support person named",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="primarySupportPerson", max_len=60),
    ),
    "PSYCH_SUPPORT_RELATIONSHIP": ConceptMapping(
        "PSYCH_SUPPORT_RELATIONSHIP", "psychosocial", "Support person relationship",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="supportRelationship", max_len=40),
    ),
    "PSYCH_CONCERN_ANXIETY_ABOUT_ILLNESS": ConceptMapping("PSYCH_CONCERN_ANXIETY_ABOUT_ILLNESS", "psychosocial", "Anxiety about illness", (_fw("patientConcerns", "Anxiety about illness", op="multi_add"),)),
    "PSYCH_CONCERN_DEPRESSION": ConceptMapping("PSYCH_CONCERN_DEPRESSION", "psychosocial", "Depression concern", (_fw("patientConcerns", "Depression", op="multi_add"),)),
    "PSYCH_CONCERN_GRIEF_LOSS": ConceptMapping("PSYCH_CONCERN_GRIEF_LOSS", "psychosocial", "Grief/loss concern", (_fw("patientConcerns", "Grief/loss", op="multi_add"),)),
    "PSYCH_CONCERN_FINANCIAL": ConceptMapping("PSYCH_CONCERN_FINANCIAL", "psychosocial", "Financial concerns", (_fw("patientConcerns", "Financial concerns", op="multi_add"),)),
    "PSYCH_CONCERN_FAMILY_CONFLICT": ConceptMapping("PSYCH_CONCERN_FAMILY_CONFLICT", "psychosocial", "Family conflict", (_fw("patientConcerns", "Family conflict", op="multi_add"),)),
    "PSYCH_CONCERN_CAREGIVER_BURDEN": ConceptMapping("PSYCH_CONCERN_CAREGIVER_BURDEN", "psychosocial", "Caregiver burden", (_fw("patientConcerns", "Caregiver burden", op="multi_add"),)),
    "PSYCH_CONCERN_SOCIAL_ISOLATION": ConceptMapping("PSYCH_CONCERN_SOCIAL_ISOLATION", "psychosocial", "Social isolation", (_fw("patientConcerns", "Social isolation", op="multi_add"),)),
    "PSYCH_CONCERN_ROLE_CHANGES": ConceptMapping("PSYCH_CONCERN_ROLE_CHANGES", "psychosocial", "Role changes", (_fw("patientConcerns", "Role changes", op="multi_add"),)),
    "PSYCH_CONCERN_UNFINISHED_BUSINESS": ConceptMapping("PSYCH_CONCERN_UNFINISHED_BUSINESS", "psychosocial", "Unfinished business", (_fw("patientConcerns", "Unfinished business", op="multi_add"),)),
    "PSYCH_CONCERN_FEAR_OF_DYING": ConceptMapping("PSYCH_CONCERN_FEAR_OF_DYING", "psychosocial", "Fear of dying", (_fw("patientConcerns", "Fear of dying", op="multi_add"),)),
    "PSYCH_CONCERN_LOSS_OF_INDEPENDENCE": ConceptMapping("PSYCH_CONCERN_LOSS_OF_INDEPENDENCE", "psychosocial", "Loss of independence", (_fw("patientConcerns", "Loss of independence", op="multi_add"),)),
    "PSYCH_CONCERN_NON_ACCEPTANCE_OF_DIAGNOSIS": ConceptMapping("PSYCH_CONCERN_NON_ACCEPTANCE_OF_DIAGNOSIS", "psychosocial", "Non-acceptance of diagnosis", (_fw("patientConcerns", "Non-acceptance of diagnosis", op="multi_add"),)),
    "PSYCH_CONCERN_SUICIDE": ConceptMapping("PSYCH_CONCERN_SUICIDE", "psychosocial", "Suicide concerns", (_fw("patientConcerns", "Suicide concerns", op="multi_add"),)),
    "PSYCH_CONCERN_SUBSTANCE_ABUSE": ConceptMapping("PSYCH_CONCERN_SUBSTANCE_ABUSE", "psychosocial", "Substance abuse concerns", (_fw("patientConcerns", "Substance abuse concerns", op="multi_add"),)),
    "PSYCH_CONCERN_HISTORY_EMOTIONAL_ILLNESS": ConceptMapping("PSYCH_CONCERN_HISTORY_EMOTIONAL_ILLNESS", "psychosocial", "History of emotional illness", (_fw("patientConcerns", "History of emotional illness", op="multi_add"),)),
    "PSYCH_CONCERN_CULTURAL": ConceptMapping("PSYCH_CONCERN_CULTURAL", "psychosocial", "Cultural concerns", (_fw("patientConcerns", "Cultural concerns", op="multi_add"),)),
    "PSYCH_CONCERN_BURIAL": ConceptMapping("PSYCH_CONCERN_BURIAL", "psychosocial", "Burial concerns", (_fw("patientConcerns", "Burial concerns", op="multi_add"),)),
    "PSYCH_CONCERN_ANGER": ConceptMapping("PSYCH_CONCERN_ANGER", "psychosocial", "Anger", (_fw("patientConcerns", "Anger", op="multi_add"),)),
    "PSYCH_CAREGIVER_ANTICIPATORY_GRIEF": ConceptMapping("PSYCH_CAREGIVER_ANTICIPATORY_GRIEF", "psychosocial", "Anticipatory grief (caregiver)", (_fw("caregiverFamilyConcerns", "Anticipatory grief", op="multi_add"),)),
    "PSYCH_CAREGIVER_FATIGUE": ConceptMapping("PSYCH_CAREGIVER_FATIGUE", "psychosocial", "Caregiver fatigue", (_fw("caregiverFamilyConcerns", "Caregiver fatigue", op="multi_add"),)),
    "PSYCH_CAREGIVER_FINANCIAL_STRESS": ConceptMapping("PSYCH_CAREGIVER_FINANCIAL_STRESS", "psychosocial", "Financial stress (caregiver)", (_fw("caregiverFamilyConcerns", "Financial stress", op="multi_add"),)),
    "PSYCH_CAREGIVER_WORK_LIFE_BALANCE": ConceptMapping("PSYCH_CAREGIVER_WORK_LIFE_BALANCE", "psychosocial", "Work-life balance concern (caregiver)", (_fw("caregiverFamilyConcerns", "Work-life balance", op="multi_add"),)),
    "PSYCH_CAREGIVER_CHILDREN_FAMILY_COPING": ConceptMapping("PSYCH_CAREGIVER_CHILDREN_FAMILY_COPING", "psychosocial", "Children/family coping concern", (_fw("caregiverFamilyConcerns", "Children/family coping", op="multi_add"),)),
    "PSYCH_CAREGIVER_FUNERAL_PLANNING": ConceptMapping("PSYCH_CAREGIVER_FUNERAL_PLANNING", "psychosocial", "Funeral planning concern (caregiver)", (_fw("caregiverFamilyConcerns", "Funeral planning", op="multi_add"),)),
    "PSYCH_CAREGIVER_ESTATE_LEGAL": ConceptMapping("PSYCH_CAREGIVER_ESTATE_LEGAL", "psychosocial", "Estate/legal matters concern (caregiver)", (_fw("caregiverFamilyConcerns", "Estate/legal matters", op="multi_add"),)),
    "PSYCH_DISTRESS_RATING": ConceptMapping(
        "PSYCH_DISTRESS_RATING", "psychosocial", "Distress Thermometer score documented",
        (), value_slot=ValueSlot(kind="numeric", path="distressRating", min_value=0, max_value=10),
    ),
    "PSYCH_HISTORY_DEPRESSION": ConceptMapping("PSYCH_HISTORY_DEPRESSION", "psychosocial", "History of depression", (_fw("psychosocialHistory", "History of depression", op="multi_add"),)),
    "PSYCH_HISTORY_ANXIETY": ConceptMapping("PSYCH_HISTORY_ANXIETY", "psychosocial", "History of anxiety", (_fw("psychosocialHistory", "History of anxiety", op="multi_add"),)),
    "PSYCH_HISTORY_SUBSTANCE_ABUSE": ConceptMapping("PSYCH_HISTORY_SUBSTANCE_ABUSE", "psychosocial", "History of substance abuse", (_fw("psychosocialHistory", "History of substance abuse", op="multi_add"),)),
    "PSYCH_CURRENT_MH_TREATMENT": ConceptMapping("PSYCH_CURRENT_MH_TREATMENT", "psychosocial", "Current mental health treatment", (_fw("psychosocialHistory", "Current mental health treatment", op="multi_add"),)),
    "PSYCH_PSYCHIATRIC_MEDICATIONS": ConceptMapping("PSYCH_PSYCHIATRIC_MEDICATIONS", "psychosocial", "Psychiatric medications", (_fw("psychosocialHistory", "Psychiatric medications", op="multi_add"),)),
    "PSYCH_PREVIOUS_COUNSELING": ConceptMapping("PSYCH_PREVIOUS_COUNSELING", "psychosocial", "Previous counseling/therapy", (_fw("psychosocialHistory", "Previous counseling/therapy", op="multi_add"),)),

    # ═══════════════════════ SPIRITUAL (real gaps) ══════════════════════════
    # `concernsDiscussedDate` is a completion date for an action, not a fact
    # about the patient -- excluded. `chaplainNeeded` is a referral decision,
    # not an extraction target -- excluded.
    "SPIRITUAL_PATIENT_ACTIVE_IN_FAITH": ConceptMapping("SPIRITUAL_PATIENT_ACTIVE_IN_FAITH", "spiritual", "Patient active in faith tradition", (_fw("patientActiveInFaithTradition", True),)),
    "SPIRITUAL_PATIENT_FAITH": ConceptMapping(
        "SPIRITUAL_PATIENT_FAITH", "spiritual", "Patient faith tradition named",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="patientFaith", max_len=60),
    ),
    "SPIRITUAL_CAREGIVER_ACTIVE_IN_FAITH": ConceptMapping("SPIRITUAL_CAREGIVER_ACTIVE_IN_FAITH", "spiritual", "Caregiver active in faith tradition", (_fw("caregiverActiveInFaithTradition", True),)),
    "SPIRITUAL_CAREGIVER_FAITH": ConceptMapping(
        "SPIRITUAL_CAREGIVER_FAITH", "spiritual", "Caregiver faith tradition named",
        (), value_slot=ValueSlot(kind="free_text_bounded", path="caregiverFaith", max_len=60),
    ),
    "SPIRITUAL_CONCERN_MEANING_OF_ILLNESS": ConceptMapping("SPIRITUAL_CONCERN_MEANING_OF_ILLNESS", "spiritual", "Meaning of illness concern", (_fw("spiritualConcerns", "Meaning of illness", op="multi_add"),)),
    "SPIRITUAL_CONCERN_FORGIVENESS": ConceptMapping("SPIRITUAL_CONCERN_FORGIVENESS", "spiritual", "Forgiveness concern", (_fw("spiritualConcerns", "Forgiveness", op="multi_add"),)),
    "SPIRITUAL_CONCERN_HOPE": ConceptMapping("SPIRITUAL_CONCERN_HOPE", "spiritual", "Hope concern", (_fw("spiritualConcerns", "Hope", op="multi_add"),)),
    "SPIRITUAL_CONCERN_LEGACY": ConceptMapping("SPIRITUAL_CONCERN_LEGACY", "spiritual", "Legacy concern", (_fw("spiritualConcerns", "Legacy", op="multi_add"),)),
    "SPIRITUAL_CONCERN_PRAYER_REQUESTS": ConceptMapping("SPIRITUAL_CONCERN_PRAYER_REQUESTS", "spiritual", "Prayer requests", (_fw("spiritualConcerns", "Prayer requests", op="multi_add"),)),
    "SPIRITUAL_CONCERN_RELIGIOUS_RITUALS": ConceptMapping("SPIRITUAL_CONCERN_RELIGIOUS_RITUALS", "spiritual", "Religious rituals concern", (_fw("spiritualConcerns", "Religious rituals", op="multi_add"),)),
    "SPIRITUAL_CONCERN_AFTERLIFE": ConceptMapping("SPIRITUAL_CONCERN_AFTERLIFE", "spiritual", "Afterlife concerns", (_fw("spiritualConcerns", "Afterlife concerns", op="multi_add"),)),
    "SPIRITUAL_CONCERN_ANGER_AT_GOD": ConceptMapping("SPIRITUAL_CONCERN_ANGER_AT_GOD", "spiritual", "Anger at God", (_fw("spiritualConcerns", "Anger at God", op="multi_add"),)),
    "SPIRITUAL_CONCERN_SPIRITUAL_DISTRESS": ConceptMapping("SPIRITUAL_CONCERN_SPIRITUAL_DISTRESS", "spiritual", "Spiritual distress", (_fw("spiritualConcerns", "Spiritual distress", op="multi_add"),)),
    "SPIRITUAL_CONCERN_FEAR": ConceptMapping("SPIRITUAL_CONCERN_FEAR", "spiritual", "Fear (spiritual)", (_fw("spiritualConcerns", "Fear", op="multi_add"),)),
    "SPIRITUAL_CONCERN_HOPELESSNESS": ConceptMapping("SPIRITUAL_CONCERN_HOPELESSNESS", "spiritual", "Hopelessness", (_fw("spiritualConcerns", "Hopelessness", op="multi_add"),)),
    "SPIRITUAL_DISTRESS_RATING": ConceptMapping(
        "SPIRITUAL_DISTRESS_RATING", "spiritual", "Spiritual distress rating documented",
        (), value_slot=ValueSlot(kind="numeric", path="spiritualDistressRating", min_value=0, max_value=10),
    ),
    "SPIRITUAL_CONCERNS_ASKED_YES_DISCUSSED": ConceptMapping("SPIRITUAL_CONCERNS_ASKED_YES_DISCUSSED", "spiritual", "F3000: asked, discussion occurred", (_fw("concernsAskedStatus", "1"), _fw("concernsDiscussed", True))),
    "SPIRITUAL_CONCERNS_ASKED_YES_REFUSED": ConceptMapping("SPIRITUAL_CONCERNS_ASKED_YES_REFUSED", "spiritual", "F3000: asked, patient refused to discuss", (_fw("concernsAskedStatus", "2"),)),
    "SPIRITUAL_CONCERNS_NOT_ASKED": ConceptMapping("SPIRITUAL_CONCERNS_NOT_ASKED", "spiritual", "F3000: not asked", (_fw("concernsAskedStatus", "0"),)),
    "SPIRITUAL_CHAPLAIN_NEEDED": ConceptMapping("SPIRITUAL_CHAPLAIN_NEEDED", "spiritual", "Chaplain referral explicitly requested/documented", (_fw("chaplainNeeded", True),)),

    # ═══════════════════════ BEREAVEMENT (real gaps) ════════════════════════
    # `bereavementVisitNeeded` is a referral/plan decision -- excluded.
    "BEREAVEMENT_PATIENT_FEAR_OF_DEATH": ConceptMapping("BEREAVEMENT_PATIENT_FEAR_OF_DEATH", "bereavement", "Fear of death (patient)", (_fw("patientConcerns", "Fear of death", op="multi_add"),)),
    "BEREAVEMENT_PATIENT_UNRESOLVED_GRIEF": ConceptMapping("BEREAVEMENT_PATIENT_UNRESOLVED_GRIEF", "bereavement", "Unresolved grief (patient)", (_fw("patientConcerns", "Unresolved grief", op="multi_add"),)),
    "BEREAVEMENT_PATIENT_EXISTENTIAL_DISTRESS": ConceptMapping("BEREAVEMENT_PATIENT_EXISTENTIAL_DISTRESS", "bereavement", "Existential distress (patient)", (_fw("patientConcerns", "Existential distress", op="multi_add"),)),
    "BEREAVEMENT_PATIENT_LEGACY_CONCERNS": ConceptMapping("BEREAVEMENT_PATIENT_LEGACY_CONCERNS", "bereavement", "Legacy concerns (patient)", (_fw("patientConcerns", "Legacy concerns", op="multi_add"),)),
    "BEREAVEMENT_PATIENT_FAMILY_PREPAREDNESS": ConceptMapping("BEREAVEMENT_PATIENT_FAMILY_PREPAREDNESS", "bereavement", "Family preparedness concern", (_fw("patientConcerns", "Family preparedness", op="multi_add"),)),
    "BEREAVEMENT_PATIENT_MULTIPLE_LOSSES": ConceptMapping("BEREAVEMENT_PATIENT_MULTIPLE_LOSSES", "bereavement", "Multiple losses (patient)", (_fw("patientConcerns", "Multiple losses", op="multi_add"),)),
    "BEREAVEMENT_PATIENT_ACTIVE_GRIEVING": ConceptMapping("BEREAVEMENT_PATIENT_ACTIVE_GRIEVING", "bereavement", "Active grieving (patient)", (_fw("patientConcerns", "Active grieving", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_ANTICIPATORY_GRIEF": ConceptMapping("BEREAVEMENT_CAREGIVER_ANTICIPATORY_GRIEF", "bereavement", "Anticipatory grief (caregiver)", (_fw("caregiverConcerns", "Anticipatory grief", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_PREVIOUS_LOSSES": ConceptMapping("BEREAVEMENT_CAREGIVER_PREVIOUS_LOSSES", "bereavement", "Previous losses (caregiver)", (_fw("caregiverConcerns", "Previous losses", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_COMPLICATED_GRIEF_HISTORY": ConceptMapping("BEREAVEMENT_CAREGIVER_COMPLICATED_GRIEF_HISTORY", "bereavement", "Complicated grief history (caregiver)", (_fw("caregiverConcerns", "Complicated grief history", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_MENTAL_HEALTH_CONCERNS": ConceptMapping("BEREAVEMENT_CAREGIVER_MENTAL_HEALTH_CONCERNS", "bereavement", "Mental health concerns (caregiver)", (_fw("caregiverConcerns", "Mental health concerns", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_SUBSTANCE_ABUSE_HISTORY": ConceptMapping("BEREAVEMENT_CAREGIVER_SUBSTANCE_ABUSE_HISTORY", "bereavement", "Substance abuse history (caregiver)", (_fw("caregiverConcerns", "Substance abuse history", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_SOCIAL_ISOLATION": ConceptMapping("BEREAVEMENT_CAREGIVER_SOCIAL_ISOLATION", "bereavement", "Social isolation (caregiver)", (_fw("caregiverConcerns", "Social isolation", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_CONCURRENT_STRESSORS": ConceptMapping("BEREAVEMENT_CAREGIVER_CONCURRENT_STRESSORS", "bereavement", "Concurrent stressors (caregiver)", (_fw("caregiverConcerns", "Concurrent stressors", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_MULTIPLE_LOSSES": ConceptMapping("BEREAVEMENT_CAREGIVER_MULTIPLE_LOSSES", "bereavement", "Multiple losses (caregiver)", (_fw("caregiverConcerns", "Multiple losses", op="multi_add"),)),
    "BEREAVEMENT_CAREGIVER_ACTIVE_GRIEVING": ConceptMapping("BEREAVEMENT_CAREGIVER_ACTIVE_GRIEVING", "bereavement", "Active grieving (caregiver)", (_fw("caregiverConcerns", "Active grieving", op="multi_add"),)),
    "BEREAVEMENT_RISK_LOW": ConceptMapping("BEREAVEMENT_RISK_LOW", "bereavement", "Bereavement risk documented as low", (_fw("bereavementRisk", "Low"),)),
    "BEREAVEMENT_RISK_MODERATE": ConceptMapping("BEREAVEMENT_RISK_MODERATE", "bereavement", "Bereavement risk documented as moderate", (_fw("bereavementRisk", "Moderate"),)),
    "BEREAVEMENT_RISK_HIGH": ConceptMapping("BEREAVEMENT_RISK_HIGH", "bereavement", "Bereavement risk documented as high", (_fw("bereavementRisk", "High"),)),

    # ═══════════════════════ PERSONAL CARE (real gaps) ══════════════════════
    # `aideVisitPreferences.*` (frequency/preferredTime/duration) are
    # scheduling/logistics preferences, not clinical facts -- deferred, not
    # in scope of this pass.
    "PERSONALCARE_AIDE_BATHING": ConceptMapping("PERSONALCARE_AIDE_BATHING", "personalCare", "Aide task: bathing/showering", (_fw("aideTasks", "Bathing/showering", op="multi_add"),)),
    "PERSONALCARE_AIDE_HAIR_GROOMING": ConceptMapping("PERSONALCARE_AIDE_HAIR_GROOMING", "personalCare", "Aide task: hair care/grooming", (_fw("aideTasks", "Hair care/grooming", op="multi_add"),)),
    "PERSONALCARE_AIDE_ORAL_HYGIENE": ConceptMapping("PERSONALCARE_AIDE_ORAL_HYGIENE", "personalCare", "Aide task: oral hygiene", (_fw("aideTasks", "Oral hygiene", op="multi_add"),)),
    "PERSONALCARE_AIDE_SKIN_CARE": ConceptMapping("PERSONALCARE_AIDE_SKIN_CARE", "personalCare", "Aide task: skin care", (_fw("aideTasks", "Skin care", op="multi_add"),)),
    "PERSONALCARE_AIDE_DRESSING": ConceptMapping("PERSONALCARE_AIDE_DRESSING", "personalCare", "Aide task: dressing", (_fw("aideTasks", "Dressing", op="multi_add"),)),
    "PERSONALCARE_AIDE_TOILETING": ConceptMapping("PERSONALCARE_AIDE_TOILETING", "personalCare", "Aide task: toileting assistance", (_fw("aideTasks", "Toileting assistance", op="multi_add"),)),
    "PERSONALCARE_AIDE_TRANSFERS_MOBILITY": ConceptMapping("PERSONALCARE_AIDE_TRANSFERS_MOBILITY", "personalCare", "Aide task: transfers/mobility", (_fw("aideTasks", "Transfers/mobility", op="multi_add"),)),
    "PERSONALCARE_AIDE_LIGHT_MEAL_PREP": ConceptMapping("PERSONALCARE_AIDE_LIGHT_MEAL_PREP", "personalCare", "Aide task: light meal preparation", (_fw("aideTasks", "Light meal preparation", op="multi_add"),)),
    "PERSONALCARE_AIDE_LIGHT_HOUSEKEEPING": ConceptMapping("PERSONALCARE_AIDE_LIGHT_HOUSEKEEPING", "personalCare", "Aide task: light housekeeping", (_fw("aideTasks", "Light housekeeping", op="multi_add"),)),
    "PERSONALCARE_AIDE_LAUNDRY": ConceptMapping("PERSONALCARE_AIDE_LAUNDRY", "personalCare", "Aide task: laundry", (_fw("aideTasks", "Laundry", op="multi_add"),)),
    "PERSONALCARE_VOLUNTEER_COMPANIONSHIP": ConceptMapping("PERSONALCARE_VOLUNTEER_COMPANIONSHIP", "personalCare", "Volunteer service: companionship/visits", (_fw("volunteerServices", "Companionship/visits", op="multi_add"),)),
    "PERSONALCARE_VOLUNTEER_RESPITE": ConceptMapping("PERSONALCARE_VOLUNTEER_RESPITE", "personalCare", "Volunteer service: respite care", (_fw("volunteerServices", "Respite care", op="multi_add"),)),
    "PERSONALCARE_VOLUNTEER_ERRANDS": ConceptMapping("PERSONALCARE_VOLUNTEER_ERRANDS", "personalCare", "Volunteer service: errand assistance", (_fw("volunteerServices", "Errand assistance", op="multi_add"),)),
    "PERSONALCARE_VOLUNTEER_TRANSPORTATION": ConceptMapping("PERSONALCARE_VOLUNTEER_TRANSPORTATION", "personalCare", "Volunteer service: transportation", (_fw("volunteerServices", "Transportation", op="multi_add"),)),
    "PERSONALCARE_VOLUNTEER_VIGIL": ConceptMapping("PERSONALCARE_VOLUNTEER_VIGIL", "personalCare", "Volunteer service: vigil/11th hour", (_fw("volunteerServices", "Vigil/11th hour", op="multi_add"),)),
    "PERSONALCARE_VOLUNTEER_PET_CARE": ConceptMapping("PERSONALCARE_VOLUNTEER_PET_CARE", "personalCare", "Volunteer service: pet care", (_fw("volunteerServices", "Pet care", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_MEALS_ON_WHEELS": ConceptMapping("PERSONALCARE_COMMUNITY_MEALS_ON_WHEELS", "personalCare", "Community resource: Meals on Wheels", (_fw("communityResources", "Meals on Wheels", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_ADULT_DAY_CARE": ConceptMapping("PERSONALCARE_COMMUNITY_ADULT_DAY_CARE", "personalCare", "Community resource: adult day care", (_fw("communityResources", "Adult day care", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_TRANSPORTATION": ConceptMapping("PERSONALCARE_COMMUNITY_TRANSPORTATION", "personalCare", "Community resource: transportation services", (_fw("communityResources", "Transportation services", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_LEGAL_AID": ConceptMapping("PERSONALCARE_COMMUNITY_LEGAL_AID", "personalCare", "Community resource: legal aid", (_fw("communityResources", "Legal aid", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_FINANCIAL_ASSISTANCE": ConceptMapping("PERSONALCARE_COMMUNITY_FINANCIAL_ASSISTANCE", "personalCare", "Community resource: financial assistance programs", (_fw("communityResources", "Financial assistance programs", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_FAITH_SUPPORT": ConceptMapping("PERSONALCARE_COMMUNITY_FAITH_SUPPORT", "personalCare", "Community resource: faith community support", (_fw("communityResources", "Faith community support", op="multi_add"),)),
    "PERSONALCARE_COMMUNITY_VETERAN_SERVICES": ConceptMapping("PERSONALCARE_COMMUNITY_VETERAN_SERVICES", "personalCare", "Community resource: veteran services", (_fw("communityResources", "Veteran services", op="multi_add"),)),
    "PERSONALCARE_EQUIP_HOSPITAL_BED": ConceptMapping("PERSONALCARE_EQUIP_HOSPITAL_BED", "personalCare", "Equipment need: hospital bed", (_fw("equipmentSupplyNeeds", "Hospital bed", op="multi_add"),)),
    "PERSONALCARE_EQUIP_WHEELCHAIR": ConceptMapping("PERSONALCARE_EQUIP_WHEELCHAIR", "personalCare", "Equipment need: wheelchair", (_fw("equipmentSupplyNeeds", "Wheelchair", op="multi_add"),)),
    "PERSONALCARE_EQUIP_WALKER": ConceptMapping("PERSONALCARE_EQUIP_WALKER", "personalCare", "Equipment need: walker", (_fw("equipmentSupplyNeeds", "Walker", op="multi_add"),)),
    "PERSONALCARE_EQUIP_COMMODE": ConceptMapping("PERSONALCARE_EQUIP_COMMODE", "personalCare", "Equipment need: commode", (_fw("equipmentSupplyNeeds", "Commode", op="multi_add"),)),
    "PERSONALCARE_EQUIP_SHOWER_CHAIR": ConceptMapping("PERSONALCARE_EQUIP_SHOWER_CHAIR", "personalCare", "Equipment need: shower chair", (_fw("equipmentSupplyNeeds", "Shower chair", op="multi_add"),)),
    "PERSONALCARE_EQUIP_HOYER_LIFT": ConceptMapping("PERSONALCARE_EQUIP_HOYER_LIFT", "personalCare", "Equipment need: Hoyer lift", (_fw("equipmentSupplyNeeds", "Hoyer lift", op="multi_add"),)),
    "PERSONALCARE_EQUIP_EGG_CRATE_MATTRESS": ConceptMapping("PERSONALCARE_EQUIP_EGG_CRATE_MATTRESS", "personalCare", "Equipment need: egg crate mattress", (_fw("equipmentSupplyNeeds", "Egg crate mattress", op="multi_add"),)),
    "PERSONALCARE_EQUIP_INCONTINENCE_SUPPLIES": ConceptMapping("PERSONALCARE_EQUIP_INCONTINENCE_SUPPLIES", "personalCare", "Equipment need: incontinence supplies", (_fw("equipmentSupplyNeeds", "Incontinence supplies", op="multi_add"),)),
    "PERSONALCARE_EQUIP_WOUND_CARE_SUPPLIES": ConceptMapping("PERSONALCARE_EQUIP_WOUND_CARE_SUPPLIES", "personalCare", "Equipment need: wound care supplies", (_fw("equipmentSupplyNeeds", "Wound care supplies", op="multi_add"),)),
    "PERSONALCARE_EQUIP_AIR_MATTRESS": ConceptMapping("PERSONALCARE_EQUIP_AIR_MATTRESS", "personalCare", "Equipment need: air mattress", (_fw("equipmentSupplyNeeds", "Air mattress", op="multi_add"),)),
    "PERSONALCARE_EQUIP_BEDPAN": ConceptMapping("PERSONALCARE_EQUIP_BEDPAN", "personalCare", "Equipment need: bedpan", (_fw("equipmentSupplyNeeds", "Bedpan", op="multi_add"),)),
    "PERSONALCARE_EQUIP_OVERBED_TABLE": ConceptMapping("PERSONALCARE_EQUIP_OVERBED_TABLE", "personalCare", "Equipment need: overbed table", (_fw("equipmentSupplyNeeds", "Overbed table", op="multi_add"),)),
    "PERSONALCARE_EQUIP_CANE": ConceptMapping("PERSONALCARE_EQUIP_CANE", "personalCare", "Equipment need: cane", (_fw("equipmentSupplyNeeds", "Cane", op="multi_add"),)),
    "PERSONALCARE_EQUIP_GERI_CHAIR": ConceptMapping("PERSONALCARE_EQUIP_GERI_CHAIR", "personalCare", "Equipment need: geri-chair/recliner", (_fw("equipmentSupplyNeeds", "Geri-chair/recliner", op="multi_add"),)),
    "PERSONALCARE_EQUIP_URINAL": ConceptMapping("PERSONALCARE_EQUIP_URINAL", "personalCare", "Equipment need: urinal", (_fw("equipmentSupplyNeeds", "Urinal", op="multi_add"),)),
    "PERSONALCARE_EQUIP_NEBULIZER": ConceptMapping("PERSONALCARE_EQUIP_NEBULIZER", "personalCare", "Equipment need: nebulizer", (_fw("equipmentSupplyNeeds", "Nebulizer", op="multi_add"),)),
    "PERSONALCARE_EQUIP_SUCTION_MACHINE": ConceptMapping("PERSONALCARE_EQUIP_SUCTION_MACHINE", "personalCare", "Equipment need: suction machine", (_fw("equipmentSupplyNeeds", "Suction machine", op="multi_add"),)),
    "PERSONALCARE_EQUIP_O2_CONCENTRATOR": ConceptMapping("PERSONALCARE_EQUIP_O2_CONCENTRATOR", "personalCare", "Equipment need: O2 concentrator", (_fw("equipmentSupplyNeeds", "O2 concentrator", op="multi_add"),)),
    "PERSONALCARE_EQUIP_E_TANK": ConceptMapping("PERSONALCARE_EQUIP_E_TANK", "personalCare", "Equipment need: E-tank", (_fw("equipmentSupplyNeeds", "E-tank", op="multi_add"),)),

    # ═══════════════════════ TEACHING NEEDS (real gaps) ═════════════════════
    # `teachingTopics`/`teachingMethods`/`patientFamilyResponse`/
    # `followUpPlan` document what THIS VISIT's RN actually taught and how
    # the patient/family responded -- that is a this-visit workflow record,
    # not an admission fact, and is excluded. Only the learner
    # CHARACTERISTICS (who the learner is, how they learn best, and any
    # documented barriers) are admission-document facts worth capturing.
    "TEACH_PRIMARY_LEARNER_PATIENT": ConceptMapping("TEACH_PRIMARY_LEARNER_PATIENT", "teachingNeeds", "Primary learner: patient", (_fw("primaryLearner", "Patient"),)),
    "TEACH_PRIMARY_LEARNER_CAREGIVER": ConceptMapping("TEACH_PRIMARY_LEARNER_CAREGIVER", "teachingNeeds", "Primary learner: caregiver", (_fw("primaryLearner", "Caregiver"),)),
    "TEACH_PRIMARY_LEARNER_BOTH": ConceptMapping("TEACH_PRIMARY_LEARNER_BOTH", "teachingNeeds", "Primary learner: both patient and caregiver", (_fw("primaryLearner", "Both"),)),
    "TEACH_LEARNING_STYLE_VISUAL": ConceptMapping("TEACH_LEARNING_STYLE_VISUAL", "teachingNeeds", "Learning style: visual", (_fw("learningStylePreference", "Visual"),)),
    "TEACH_LEARNING_STYLE_AUDITORY": ConceptMapping("TEACH_LEARNING_STYLE_AUDITORY", "teachingNeeds", "Learning style: auditory", (_fw("learningStylePreference", "Auditory"),)),
    "TEACH_LEARNING_STYLE_HANDS_ON": ConceptMapping("TEACH_LEARNING_STYLE_HANDS_ON", "teachingNeeds", "Learning style: hands-on", (_fw("learningStylePreference", "Hands-on"),)),
    "TEACH_LEARNING_STYLE_WRITTEN": ConceptMapping("TEACH_LEARNING_STYLE_WRITTEN", "teachingNeeds", "Learning style: written materials", (_fw("learningStylePreference", "Written materials"),)),
    "TEACH_BARRIER_LANGUAGE": ConceptMapping("TEACH_BARRIER_LANGUAGE", "teachingNeeds", "Learning barrier: language", (_fw("barriersToLearning", "Language", op="multi_add"),)),
    "TEACH_BARRIER_LITERACY": ConceptMapping("TEACH_BARRIER_LITERACY", "teachingNeeds", "Learning barrier: literacy", (_fw("barriersToLearning", "Literacy", op="multi_add"),)),
    "TEACH_BARRIER_COGNITIVE_IMPAIRMENT": ConceptMapping("TEACH_BARRIER_COGNITIVE_IMPAIRMENT", "teachingNeeds", "Learning barrier: cognitive impairment", (_fw("barriersToLearning", "Cognitive impairment", op="multi_add"),)),
    "TEACH_BARRIER_HEARING_DEFICIT": ConceptMapping("TEACH_BARRIER_HEARING_DEFICIT", "teachingNeeds", "Learning barrier: hearing deficit", (_fw("barriersToLearning", "Hearing deficit", op="multi_add"),)),
    "TEACH_BARRIER_VISION_DEFICIT": ConceptMapping("TEACH_BARRIER_VISION_DEFICIT", "teachingNeeds", "Learning barrier: vision deficit", (_fw("barriersToLearning", "Vision deficit", op="multi_add"),)),
    "TEACH_BARRIER_CULTURAL_CONSIDERATIONS": ConceptMapping("TEACH_BARRIER_CULTURAL_CONSIDERATIONS", "teachingNeeds", "Learning barrier: cultural considerations", (_fw("barriersToLearning", "Cultural considerations", op="multi_add"),)),
    "TEACH_BARRIER_DENIAL_OF_DIAGNOSIS": ConceptMapping("TEACH_BARRIER_DENIAL_OF_DIAGNOSIS", "teachingNeeds", "Learning barrier: denial of diagnosis", (_fw("barriersToLearning", "Denial of diagnosis", op="multi_add"),)),
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
