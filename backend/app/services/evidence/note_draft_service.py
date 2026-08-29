"""AI-drafted clinical narrative from a visit recording's transcript.

Design contract (same shape as ai_extraction_service.py):
    - NEVER raises. Any failure (not configured, network error, malformed
      model output) is logged and results in `None` -- the caller always
      still preserves the transcript itself untouched.
    - NEVER auto-applies anything to a chart record. This module only
      produces a candidate narrative for a clinician to review, edit, and
      explicitly insert into the RNICA note -- the insertion itself is a
      separate, human-triggered action in the frontend.
    - NEVER fabricates. The system prompt requires every sentence to be
      grounded in the transcript; nothing invented is acceptable in a
      clinical record draft.

Required environment variables (already used by ai_extraction_service.py --
shared Azure OpenAI deployment, no additional configuration needed):
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_API_VERSION
    AZURE_OPENAI_DEPLOYMENT
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.evidence.structured_findings import concept_prompt_catalog, validate_findings

logger = logging.getLogger("sns_emr")

DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_TRANSCRIPT_CHARS = 12000


@dataclass(frozen=True)
class NoteDraft:
    narrative: str
    detected_topics: tuple[str, ...]
    generated_at: str
    model: str
    section_notes: dict[str, str] = field(default_factory=dict)
    symptom_severity: dict[str, str] = field(default_factory=dict)
    # Structured RNICA checkbox/dropdown/radio field suggestions derived from
    # the transcript, validated against the shared, server-controlled
    # concept vocabulary in app.services.evidence.structured_findings
    # (CONCEPT_REGISTRY / validate_findings). Each entry is a validated
    # StructuredFinding.to_dict() -- the model NEVER emits a raw field_path;
    # it only emits a concept_code from that fixed registry, which this
    # module then resolves server-side. Never auto-applied here -- purely a
    # candidate list for the frontend to apply (blank-only, with
    # provenance), same pattern as symptom_severity above but covering the
    # full structured-field surface instead of just the 6 HOPE J2051
    # severities.
    structured_findings: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "narrative": self.narrative,
            "detected_topics": list(self.detected_topics),
            "generated_at": self.generated_at,
            "model": self.model,
            "section_notes": dict(self.section_notes),
            "symptom_severity": dict(self.symptom_severity),
            "structured_findings": [dict(f) for f in self.structured_findings],
        }


def _azure_openai_config() -> dict[str, str] | None:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not (endpoint and api_key and api_version and deployment):
        return None

    return {
        "endpoint": endpoint.rstrip("/"),
        "api_key": api_key,
        "api_version": api_version,
        "deployment": deployment,
    }


def is_note_draft_configured() -> bool:
    return _azure_openai_config() is not None


_SYSTEM_PROMPT = """You are a hospice clinical documentation assistant. You read the \
transcript of an audio recording made by a hospice clinician during a patient visit \
and draft candidate clinical documentation text to help the clinician fill in the \
RN Initial Comprehensive Assessment (RNICA) note faster.

Non-negotiable rules:
- You NEVER diagnose. You NEVER invent a plan of care, orders, medication changes, or \
clinical scores/scales (e.g. never invent a Braden score, PPS/KPS number, or pain \
severity rating -- those remain the clinician's own clinical judgment to enter).
- You NEVER fabricate content that is not present in the transcript. If a topic/section \
is not discussed in the transcript, omit it entirely rather than guessing or padding.
- Write each piece of text in clinical, third-person, professional documentation style \
(e.g. "Patient reports...", "Caregiver states...", "Comfort measures discussed include...").
- If the transcript is unclear, garbled, or too short to summarize meaningfully, return \
an empty narrative and empty section_notes rather than guessing.
- Do NOT just restate the whole transcript as one long narrative paragraph and leave \
section_notes sparse/empty. Every distinct clinical topic actually discussed (a wound, a pain \
complaint, a respiratory symptom, a medication/comfort concern, a psychosocial/caregiver detail, \
a functional limitation, etc.) belongs in its OWN section_notes entry under the single most \
specific matching key, in addition to being mentioned in the narrative summary.
- NEVER compress specific clinical detail into a vaguer, more generic restatement. This is the \
single most important rule and the most common failure mode -- preserve every clinically \
meaningful specific the transcript actually gives you: exact anatomic location(s), stage/severity \
descriptors, laterality (left/right), frequency/timing, medication names and dosing intervals, \
named individuals and their role/relationship/location, and the precise nature of a functional \
limitation. Concretely:
  * WRONG: "Patient reported shortness of breath." (dropped "always", "while speaking", "at rest")
    RIGHT: "Patient reports shortness of breath at rest and while speaking; described as \
    persistent/constant."
  * WRONG: "Multiple pressure ulcers reported." (dropped stage, location)
    RIGHT: "Multiple pressure ulcers noted, including stage 2 and stage 3 areas to the coccyx \
    and right heel."
  * WRONG: "Caregiver support identified." (dropped names/roles/locations)
    RIGHT: "Brother, who resides in Florida, is identified as decision-maker; daughter visits \
    from the High Desert."
  * WRONG: "Limited arm movement." (dropped stiffness, degree)
    RIGHT: "Patient reports stiffness and inability to move the arm well."
  Only compress/omit filler, verbal tics, and repetition -- never compress away a clinical fact. \
  If you are unsure whether a detail is clinically meaningful, KEEP IT rather than drop it. The \
  output must read like a hospice nursing assessment written by someone who listened to the \
  whole visit, not a discharge-summary skim.
- The narrative is a TRANSFORMATION of the transcript into clinical documentation, not a \
  condensation of it -- every clinically relevant statement in the transcript must have a \
  corresponding, at-least-as-detailed statement in the narrative. When you also add clinical \
  significance/functional/risk context (per the rule below), the narrative should typically end \
  up LONGER than the raw transcript passage it is drawn from, never shorter. Concretely: your \
  narrative's word count must be GREATER than the transcript's word count. If, before \
  responding, your draft narrative is shorter than or about the same length as the transcript, \
  that is proof you summarized instead of documented -- go back through the transcript topic by \
  topic, restore every dropped detail, and add the clinical-significance context for each finding \
  until the narrative is unambiguously longer and richer than the transcript, not merely \
  reworded.
- Write like an experienced hospice RN charting a clinical picture, not a transcriptionist. Avoid \
  reflexively hedging every sentence with "reported"/"stated"/"states that" -- use direct clinical \
  phrasing for observed/documented findings (e.g. "Stage 2 and stage 3 pressure injuries are \
  present to the coccyx and right heel" rather than "patient reported pressure ulcers"), and \
  reserve attribution verbs ("reports", "states", "per patient/caregiver") for genuinely \
  subjective complaints, opinions, or self-reported history where attribution matters clinically \
  (e.g. pain, dyspnea, preferences, refusals). Do not overuse any single verb -- vary phrasing \
  naturally the way a skilled RN would when charting.
- Where the transcript supports it, briefly connect findings to their clinical significance and \
  functional/prognostic relevance using standard, well-established hospice/nursing correlations \
  ONLY -- do not invent new diagnoses, do not assign or imply a specific prognosis/life \
  expectancy, and do not invent facts not present in the transcript. This means describing the \
  ordinary clinical relationship between findings that are already documented, e.g.: bedbound \
  status and immobility increasing pressure injury/skin breakdown risk and dependence for all \
  care needs; dyspnea at rest and with minimal exertion (such as speaking) as a marker of \
  advancing cardiopulmonary decline and reduced functional reserve; opioid use and constipation \
  as an expected medication-related effect; stiffness/reduced range of motion after stroke \
  limiting self-care and mobility. Keep these connections brief (a clause or one sentence per \
  finding) and grounded strictly in what was actually discussed -- this is standard hospice \
  nursing narrative reasoning, not a new clinical judgment, diagnosis, prognosis certification, \
  or score.
- QUALITY BAR: a real, well-written hospice visit narrative is organized system-by-system with \
  concrete, specific, quantified detail wherever the transcript gives you the material for it -- \
  e.g. exact medication name/dose/route/frequency tied to the symptom it addresses, specific \
  wound stage(s) and anatomic location(s), specific functional/mobility status, specific \
  intake/appetite detail, specific caregiver teaching topics actually covered, specific safety/fall \
  precautions discussed, named individuals and their role. Do not settle for a single generic \
  sentence per topic when the transcript supports more specificity. Cover every clinically \
  relevant system actually touched on in the transcript (cardiovascular, respiratory, GI/nutrition, \
  GU, skin, musculoskeletal, neuro/mental status, psychosocial, safety, medications/teaching) \
  rather than only the two or three most obvious topics -- a thin narrative that only restates the \
  patient's chief complaints is a failure even if every sentence in it is technically accurate; \
  the standard is a full, dense clinical picture built from everything actually said, not a \
  highlight reel.

You produce TWO things:
1. "narrative": one overall clinical narrative paragraph documenting the whole visit \
(for the note's Clinical Narrative field).
2. "section_notes": an object mapping EVERY RNICA documentation section actually discussed in \
the transcript to a short free-text note for that section -- decompose the transcript into as \
many of these sections as genuinely apply rather than leaving everything in one narrative \
paragraph; the narrative is a high-level summary, section_notes is where the real, actionable, \
per-topic documentation goes so the clinician doesn't have to manually re-split it themselves. \
Only use these exact keys (omit any not discussed): "cardiovascular", "respiratory", \
"gastrointestinal", "nutrition", "genitourinary", "musculoskeletal", "skin", "safety", \
"psychosocial", "neurological", "functionalDeclineNotes", "infection", "endocrine", \
"imminentDeath", "sfv", "spiritual", "bereavement", "personalCare", "teachingNeeds", \
"referrals", "pain".
3. "detected_topics": a short list (any subset, none if not applicable) from this fixed \
set only: "pain", "respiratory", "skin_wound", "nutrition", "safety_fall_risk", \
"cognitive", "cardiac", "functional_decline", "caregiver_support", "medication".
4. "symptom_severity": an object rating specific HOPE J2051 symptoms on a 0-3 scale \
(0=None, 1=Mild, 2=Moderate, 3=Severe), but ONLY when the transcript makes the severity \
level clearly, unambiguously inferable -- omit a symptom's key entirely (do not guess a \
default) whenever the transcript only mentions the symptom's presence without enough \
context to grade it. This is a graded clinical judgment, so hold it to a much higher bar \
of evidence than the narrative/section_notes: you need concrete, explicit language, not \
just "patient has pain" or "patient is nauseated". Valid keys and the kind of transcript \
evidence that justifies each level:
  * "pain" -- Consider: explicit severity words ("severe", "excruciating", "constant/always \
    in pain", "unbearable" => 3/Severe; "manageable", "comes and goes", "occasional" => \
    1/Mild); OR a clear undertreatment/escalation signal -- e.g. the patient/facility is \
    already dosing an opioid at or above its usual frequency ceiling (such as Norco roughly \
    every 4 hours) AND the clinician explicitly states the current medication is/may be \
    insufficient, OR the clinician reports asking the physician to escalate to a stronger \
    opioid (e.g. Norco to morphine) -- this specific combination (frequent/maxed current \
    opioid dosing + an explicit insufficiency/escalation-seeking statement) reliably \
    indicates 3/Severe, uncontrolled pain. Do NOT infer severity from the mere fact that a \
    patient is on an opioid, or from pain being mentioned with no severity/undertreatment \
    language at all -- omit "pain" in that case.
  * "shortnessOfBreath" -- e.g. "SOB at rest", "always catching his breath", "can't finish a \
    sentence" => 2/Moderate or 3/Severe; "SOB only with exertion"/"gets a little winded" => \
    1/Mild. Omit if breathing is not discussed or only vaguely mentioned.
  * "nausea", "vomiting", "diarrhea", "constipation" -- e.g. "severe constipation", \
    "vomiting multiple times a day", "constant nausea" => 2/Moderate or 3/Severe; a single \
    mild/occasional episode => 1/Mild. Omit whichever of these was not discussed.
Only include a key in "symptom_severity" when you are confident in the rating; when in \
doubt, omit the key rather than guess -- the clinician will always be able to grade it \
manually, but a wrong AI-asserted severity is worse than a blank field.

5. "structured_findings": a list of concept-coded structured assessment findings, used to \
auto-populate the RNICA's actual checkboxes/dropdowns/radios/numeric fields (not just narrative \
text) when the transcript clearly supports a specific, discrete clinical fact. You do NOT choose \
which chart field to write, and you do NOT invent your own codes -- you may ONLY use a \
concept_code from the fixed catalog below. Any concept not in this catalog does not exist; do \
not approximate with the nearest one if it isn't a genuine match. Emit one object per distinct \
finding:
{"concept_code": "<EXACT_CODE_FROM_CATALOG>", "value": <true|false|number, per that code's \
requirement -- omit if the concept has no value_slot>, "source_excerpt": "<verbatim transcript \
quote that supports this, required>", "confidence": <0.0-1.0>, "assertion_status": \
"CURRENT|HISTORICAL|NEGATED|UNCERTAIN", "subject": "PATIENT|FAMILY|OTHER"}
Rules for structured_findings:
- "assertion_status" is mandatory and must be exact: CURRENT (true now, stated or clearly implied \
as the patient's present state), HISTORICAL (past/resolved, e.g. "history of...", "prior...", \
"resolved", a specific past date), NEGATED (explicitly denied/ruled out, e.g. "not using oxygen", \
"no chest pain", "denies..."), UNCERTAIN (ambiguous, hedged, or you cannot confidently tell which \
of the above applies).
- Only emit a concept when the transcript gives you an actual excerpt to quote as source_excerpt \
-- never emit a finding you cannot ground in a real quote.
- Do not invent a numeric value (e.g. liters/minute) beyond what a concept's value_slot allows -- \
if the transcript doesn't state the number, omit that concept entirely rather than guess one.
- Do not infer or upgrade severity/type beyond exactly what was said -- e.g. "oxygen" alone with \
no device/rate mentioned is NOT enough to assert a specific device concept.
- Never emit a "negative"/"none" finding just because a topic wasn't mentioned; NEGATED is only \
for an explicit denial actually present in the transcript.
- history mentioned only in passing with no bearing on current status should be HISTORICAL, not \
CURRENT, even if it sounds clinically important -- e.g. "history of septic shock, resolved" is \
HISTORICAL, not a current infection.
- When in doubt about whether a finding qualifies at all, omit it -- a missed structured finding \
is far less harmful than a wrong one.

CONCEPT CATALOG (the only concept_code values you may ever use):
%%CONCEPT_CATALOG%%

Respond ONLY with JSON of the exact shape:
{"narrative": "<paragraph text>", "section_notes": {"<section_key>": "<note text>", ...}, "detected_topics": ["<topic>", ...], "symptom_severity": {"<symptom_key>": "<0|1|2|3>", ...}, "structured_findings": [{"concept_code": "...", "value": "...", "source_excerpt": "...", "confidence": 0.0, "assertion_status": "...", "subject": "..."}]}
"""

# Rendered once at import time (the registry is static) rather than
# recomputed on every call.
_SYSTEM_PROMPT = _SYSTEM_PROMPT.replace("%%CONCEPT_CATALOG%%", concept_prompt_catalog())


ALLOWED_SECTION_NOTE_KEYS = {
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "nutrition",
    "genitourinary",
    "musculoskeletal",
    "skin",
    "safety",
    "psychosocial",
    "neurological",
    "functionalDeclineNotes",
    "infection",
    "endocrine",
    "imminentDeath",
    "sfv",
    "spiritual",
    "bereavement",
    "personalCare",
    "teachingNeeds",
    "referrals",
    "pain",
}

_ALLOWED_SYMPTOM_SEVERITY_KEYS = {
    "pain",
    "shortnessOfBreath",
    "nausea",
    "vomiting",
    "diarrhea",
    "constipation",
}


# IDG discipline narratives are a single free-text field per discipline
# (see IDGNote.note) -- there is no section split like RNICA. The prompt
# is parameterized by the recording's own discipline so the draft stays
# inside that discipline's clinical lens and never blends in another
# discipline's assessment content (e.g. a nurse's IDG recording must not
# draft social-work or spiritual-care language, and vice versa).
_IDG_SYSTEM_PROMPT_TEMPLATE = """You are a hospice clinical documentation assistant. You read the \
transcript of an audio recording made by a {discipline_label} during or ahead of an \
Interdisciplinary Group (IDG) review, and draft a candidate discipline narrative for that \
clinician's IDG note -- the short summary their discipline contributes to the team's review \
of this patient (e.g. current status, changes since last review, concerns to raise, plan \
input) for THIS discipline only.

Non-negotiable rules:
- You ONLY draft content that belongs to the {discipline_label}'s own discipline. Never draft \
content that belongs to a different discipline's assessment (for example: never draft social-work, \
psychosocial, financial, or caregiver-burden content unless the recording is explicitly from \
Social Work; never draft spiritual/existential/faith content unless the recording is explicitly \
from Spiritual Care; never draft nursing clinical assessment content unless the recording is \
explicitly from Nursing).
- You NEVER diagnose. You NEVER invent a plan of care, orders, medication changes, terminal \
prognosis statements, or clinical scores/scales -- those remain the clinician's own judgment.
- You NEVER fabricate content that is not present in the transcript. If the transcript does not \
contain anything relevant to this discipline's IDG contribution, return an empty narrative rather \
than guessing or padding.
- Write in clinical, third-person, professional documentation style, as a short paragraph (2-5 \
sentences) suitable to paste directly into an IDG discipline note field.
- If the transcript is unclear, garbled, or too short to summarize meaningfully, return an empty \
narrative rather than guessing.

Respond ONLY with JSON of the exact shape:
{{"narrative": "<paragraph text, or empty string>", "detected_topics": ["<topic>", ...]}}
"""

# Generic routine visit note (VisitNoteEditor / visit_notes.narrative) --
# used by every discipline that doesn't have its own dedicated ICA/RNICA
# form (CHHA, LVN, NP, MD, PA, and routine follow-up visits for RN/MSW/SC).
# Same discipline-lock contract as IDG: stays inside the recording
# clinician's own discipline lens, single narrative field, no sections.
_VISIT_NOTE_SYSTEM_PROMPT_TEMPLATE = """You are a hospice clinical documentation assistant. You \
read the transcript of an audio recording made by a {discipline_label} during a routine hospice \
visit and draft a candidate narrative for that visit's note.

Non-negotiable rules:
- You ONLY draft content that belongs to the {discipline_label}'s own discipline and scope of \
practice for this visit type. Never draft content that belongs to a different discipline's \
assessment (e.g. a nursing aide's visit note must not draft clinical assessment/medication \
content; a physician/NP/PA visit note may include clinical assessment and plan; a social work or \
spiritual care visit note must stay in that discipline's own lens).
- You NEVER diagnose beyond what the transcript explicitly states. You NEVER invent a plan of \
care, orders, medication changes, or clinical scores/scales -- those remain the clinician's own \
judgment.
- You NEVER fabricate content that is not present in the transcript. If the transcript is too \
sparse to summarize meaningfully, return an empty narrative rather than guessing or padding.
- Write in clinical, third-person, professional documentation style, as a short paragraph (2-6 \
sentences) suitable to paste directly into the visit note's Narrative field.
- If the transcript is unclear, garbled, or too short to summarize meaningfully, return an empty \
narrative rather than guessing.

Respond ONLY with JSON of the exact shape:
{{"narrative": "<paragraph text, or empty string>", "detected_topics": ["<topic>", ...]}}
"""

_IDG_DISCIPLINE_LABELS = {
    "RN": "Registered Nurse",
    "LVN": "Licensed Vocational Nurse",
    "LPN": "Licensed Practical Nurse",
    "CHHA": "Certified Home Health Aide",
    "AIDE": "Home Health Aide",
    "MSW": "Medical Social Worker",
    "SW": "Social Worker",
    "BSW": "Social Worker",
    "LCSW": "Licensed Clinical Social Worker",
    "SC": "Spiritual Care Counselor",
    "CHAPLAIN": "Chaplain",
    "MD": "Physician",
    "DO": "Physician",
    "NP": "Nurse Practitioner",
    "PA": "Physician Assistant",
    "MEDICAL_DIRECTOR": "Medical Director",
    "ATTENDING_PHYSICIAN": "Attending Physician",
}


# MSW ICA (Medical Social Worker Initial Comprehensive Assessment) has its
# own section vocabulary, strictly social-work scoped -- never clinical
# (RNICA) or spiritual (SC ICA) content.
_MSW_ICA_SYSTEM_PROMPT = """You are a hospice documentation assistant. You read the transcript \
of an audio recording made by a Medical Social Worker (MSW) during a patient/family visit and \
draft candidate documentation text to help the MSW fill in the Social Work Initial Comprehensive \
Assessment (MSW ICA) note faster.

Non-negotiable rules:
- You ONLY draft social-work-scoped content: psychosocial functioning, family dynamics/coping, \
caregiver capacity, financial/legal/advance-directive concerns, and community/referral needs.
- You NEVER draft clinical nursing content (physical/medical symptoms, wounds, medications, vital \
signs) or spiritual/existential/faith content -- those belong to other disciplines' own notes.
- You NEVER diagnose, invent a plan of care, or invent risk/rating scores -- those remain the \
social worker's own judgment.
- You NEVER fabricate content not present in the transcript. If a topic is not discussed, omit it \
entirely rather than guessing or padding.
- Write in clinical, third-person, professional documentation style (e.g. "Patient reports...", \
"Family states...").
- If the transcript is unclear, garbled, or too short to summarize meaningfully, return an empty \
narrative and empty section_notes rather than guessing.

You produce TWO things:
1. "narrative": one overall narrative paragraph summarizing the visit's social-work-relevant \
content (for the note's main Narrative field).
2. "section_notes": an object mapping ONLY the MSW ICA sections actually discussed to a short \
free-text note for that section. Only use these exact keys (omit any not discussed): \
"psychosocial" (family dynamics, living situation, support system, coping), "familyDistress" \
(family/caregiver response, anxiety, crisis), "financialLegal" (financial needs, advance \
directives, burial plans), "referrals" (community programs, therapy, volunteer services), "pain" \
(only the patient/family's subjective report of comfort -- never a clinical rating).
3. "detected_topics": a short list (any subset, none if not applicable) from this fixed set only: \
"caregiver_burden", "financial_concern", "advance_directive", "social_isolation", \
"family_conflict", "bereavement_risk", "community_referral".

Respond ONLY with JSON of the exact shape:
{"narrative": "<paragraph text>", "section_notes": {"<section_key>": "<note text>", ...}, "detected_topics": ["<topic>", ...]}
"""

_MSW_ALLOWED_SECTION_NOTE_KEYS = {"psychosocial", "familyDistress", "financialLegal", "referrals", "pain"}


# SC ICA (Spiritual Care Initial Comprehensive Assessment) has no section
# split in the form itself (a single narrative.note field) -- strictly
# spiritual/existential scoped, never clinical or psychosocial content.
_SC_ICA_SYSTEM_PROMPT = """You are a hospice documentation assistant. You read the transcript of \
an audio recording made by a Spiritual Care Counselor/Chaplain (SC) during a patient/family visit \
and draft a candidate narrative to help fill in the Spiritual Care Initial Comprehensive \
Assessment (SC ICA) note faster.

Non-negotiable rules:
- You ONLY draft spiritual-care-scoped content: faith/meaning, spiritual distress or coping, \
existential concerns, religious/faith community involvement, spiritual support provided.
- You NEVER draft clinical nursing content (physical/medical symptoms, medications) or \
social-work content (financial, legal, caregiver logistics) -- those belong to other disciplines' \
own notes.
- You NEVER diagnose, invent a plan of care, or invent a terminal prognosis statement -- those \
remain the clinician's own judgment.
- You NEVER fabricate content not present in the transcript. If nothing spiritually relevant was \
discussed, return an empty narrative rather than guessing or padding.
- Write in clinical, third-person, professional documentation style, as a short paragraph (2-5 \
sentences) suitable to paste directly into the SC ICA narrative field.
- If the transcript is unclear, garbled, or too short to summarize meaningfully, return an empty \
narrative rather than guessing.

Respond ONLY with JSON of the exact shape:
{"narrative": "<paragraph text, or empty string>", "detected_topics": ["<topic>", ...]}
"""


def generate_note_draft(
    *,
    transcript_text: str,
    assessment_type: str | None = None,
    discipline: str | None = None,
    harvested_context: str | None = None,
    admission_context: str | None = None,
) -> NoteDraft | None:
    """Generate a candidate clinical narrative from a recording's transcript.

    `assessment_type` selects the prompt/output shape:
      - "IDG": a single discipline-scoped narrative (no section_notes), using
        `discipline` (an app.models.enums.Discipline value, e.g. "MSW", "SC",
        "RN") to keep the draft strictly inside that discipline's lens.
      - "MSW_ICA": social-work-scoped narrative + section_notes (its own
        section vocabulary -- psychosocial/familyDistress/financialLegal/
        referrals/pain).
      - "SC_ICA": spiritual-care-scoped narrative only (no section_notes --
        the SC ICA form has a single narrative field).
      - "VISIT_NOTE": generic discipline-locked narrative only, for the
        routine visit note used by disciplines with no dedicated ICA/RNICA
        form (CHHA, LVN, NP, MD, PA, and routine RN/MSW/SC follow-ups).
      - anything else (default, e.g. "RNICA"/"RN_RECERT"): the existing RNICA
        narrative + section_notes shape.

    `harvested_context` is an optional compact bullet list of clinical
    findings already harvested from this patient's previously uploaded
    documents (e.g. the intake H&P) -- most of the durable clinical evidence
    for a hospice patient typically comes from the H&P, not from any single
    visit conversation, so the voice-recording draft should build on/confirm
    that prior record rather than pretend it doesn't exist. Purely additive
    context; never required, never fabricated if absent.

    `admission_context` is an optional compact fact block (patient name,
    DOB, primary/terminal diagnosis, comorbidities, decision maker, and
    certifying physician) built by `build_admission_narrative_context`.
    When present (admission/RNICA assessments only -- never RN_RECERT),
    the narrative should open by framing this as an admission, using only
    the facts actually supplied here. Purely additive; never required,
    never fabricated if absent.

    Returns None if not configured, transcript is empty, or generation
    fails for any reason -- never raises.
    """

    config = _azure_openai_config()
    if config is None:
        return None

    cleaned = (transcript_text or "").strip()
    if not cleaned:
        return None

    truncated = cleaned[:MAX_TRANSCRIPT_CHARS]

    normalized_type = (assessment_type or "").upper()
    is_idg = normalized_type == "IDG"
    is_visit_note = normalized_type == "VISIT_NOTE"
    is_msw_ica = normalized_type == "MSW_ICA"
    is_sc_ica = normalized_type == "SC_ICA"
    # Only RNICA/RN_RECERT (the default/else branch) and MSW_ICA use section_notes.
    is_sectioned = not is_idg and not is_visit_note and not is_sc_ica
    # structured_findings (concept-coded field autofill) is scoped to RNICA/RN_RECERT
    # only for now -- MSW_ICA/SC_ICA/IDG/VISIT_NOTE forms don't have the matching
    # structured controls this registry targets.
    is_rnica = is_sectioned and not is_msw_ica

    if is_idg:
        discipline_label = _IDG_DISCIPLINE_LABELS.get((discipline or "").upper(), discipline or "clinician")
        system_prompt = _IDG_SYSTEM_PROMPT_TEMPLATE.format(discipline_label=discipline_label)
        allowed_keys: set[str] = set()
    elif is_visit_note:
        discipline_label = _IDG_DISCIPLINE_LABELS.get((discipline or "").upper(), discipline or "clinician")
        system_prompt = _VISIT_NOTE_SYSTEM_PROMPT_TEMPLATE.format(discipline_label=discipline_label)
        allowed_keys = set()
    elif is_msw_ica:
        system_prompt = _MSW_ICA_SYSTEM_PROMPT
        allowed_keys = _MSW_ALLOWED_SECTION_NOTE_KEYS
    elif is_sc_ica:
        system_prompt = _SC_ICA_SYSTEM_PROMPT
        allowed_keys = set()
    else:
        system_prompt = _SYSTEM_PROMPT
        allowed_keys = ALLOWED_SECTION_NOTE_KEYS

    url = (
        f"{config['endpoint']}/openai/deployments/{config['deployment']}"
        f"/chat/completions?api-version={config['api_version']}"
    )
    user_content_parts = [f"--- VISIT RECORDING TRANSCRIPT ---\n{truncated}"]
    cleaned_admission = (admission_context or "").strip()
    if cleaned_admission and is_rnica:
        user_content_parts.append(
            "--- ADMISSION FACTS (this is an ADMISSION assessment -- the patient is being newly "
            "admitted to hospice, not a routine follow-up) ---\n"
            f"{cleaned_admission[:MAX_TRANSCRIPT_CHARS]}\n\n"
            "Open the narrative by framing this visit as the hospice admission, analogous to: "
            "\"Admitted [name]... under [level of care]... with terminal diagnosis of [dx] with "
            "comorbidities of [list]... referred to hospice with [MD] certifying... consents signed "
            "by [decision maker].\" Use ONLY the facts actually listed above -- if a fact (e.g. "
            "certifying physician, decision maker) is not listed here, omit that clause entirely "
            "rather than inventing a name or guessing. After that opening framing, continue with the "
            "rest of the narrative built from the transcript and prior findings as usual."
        )
    cleaned_harvested = (harvested_context or "").strip()
    if cleaned_harvested:
        user_content_parts.append(
            "--- PRIOR HARVESTED FINDINGS (already on file for this patient, extracted from "
            "previously uploaded documents such as the intake H&P -- NOT said in this recording) ---\n"
            f"{cleaned_harvested[:MAX_TRANSCRIPT_CHARS]}\n\n"
            "Most of the durable clinical evidence for a hospice patient typically comes from the "
            "H&P/intake documentation, not from any single visit conversation -- a spoken visit is "
            "usually confirming, following up on, or adding to that record, not re-establishing it "
            "from scratch. Use the prior findings above to enrich the narrative and section_notes: "
            "incorporate clinically relevant history, diagnoses, and findings from this list that "
            "are relevant context for what's being discussed, even if they were not repeated in the "
            "transcript. When a detail comes ONLY from this prior-findings block and was not said in "
            "the transcript, phrase it with clear attribution (e.g. 'per H&P', 'previously "
            "documented', 'per prior intake documentation') so it reads as established history being "
            "carried forward, not as something newly reported in this visit. Each item below carries "
            "its own source and, where available, a verbatim quote in double quotes -- when a quote is "
            "present, prefer weaving that specific language into the narrative (e.g. facility "
            "documentation stating patient is \"always catching his breath when speaking\") rather than "
            "a generic paraphrase; this makes the note traceable back to real documentation instead of "
            "an unsupported restatement. Never invent anything beyond what is listed here or in the "
            "transcript, and never let this list crowd out or shorten what the transcript itself says "
            "-- the transcript is still the primary source for this visit's own findings."
        )
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(user_content_parts)},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        response = httpx.post(
            url,
            headers={"api-key": config["api_key"], "Content-Type": "application/json"},
            json=payload,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        raw_content = body["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
    except Exception:
        logger.exception("note_draft_service: AI note draft generation call failed")
        return None

    if not isinstance(parsed, dict):
        return None

    narrative = str(parsed.get("narrative") or "").strip()

    section_notes: dict[str, str] = {}
    if is_sectioned:
        section_notes_raw = parsed.get("section_notes")
        if isinstance(section_notes_raw, dict):
            for key, value in section_notes_raw.items():
                if key not in allowed_keys:
                    continue
                text = str(value or "").strip()
                if text:
                    section_notes[key] = text

    if not narrative and not section_notes:
        return None

    topics_raw = parsed.get("detected_topics")
    topics = tuple(str(t).strip() for t in topics_raw if str(t).strip()) if isinstance(topics_raw, list) else ()

    symptom_severity: dict[str, str] = {}
    if is_sectioned and not is_msw_ica:
        severity_raw = parsed.get("symptom_severity")
        if isinstance(severity_raw, dict):
            for key, value in severity_raw.items():
                if key not in _ALLOWED_SYMPTOM_SEVERITY_KEYS:
                    continue
                text = str(value).strip()
                if text in {"0", "1", "2", "3"}:
                    symptom_severity[key] = text

    structured_findings: tuple[dict[str, Any], ...] = ()
    if is_rnica:
        findings_raw = parsed.get("structured_findings")
        validated = validate_findings(
            findings_raw,
            source_type="TRANSCRIPT",
            model_version=config["deployment"],
        )
        structured_findings = tuple(f.to_dict() for f in validated)

    return NoteDraft(
        narrative=narrative,
        detected_topics=topics,
        generated_at=datetime.now(timezone.utc).isoformat(),
        model=config["deployment"],
        section_notes=section_notes,
        symptom_severity=symptom_severity,
        structured_findings=structured_findings,
    )


def build_admission_narrative_context(db: Any, patient_id: Any, *, assessment_type: str | None = None) -> str:
    """Build a compact "admission framing" fact block (name, DOB, primary
    diagnosis, comorbidities, decision maker, certifying MD) so an ADMISSION
    voice-recording draft (RNICA, never RN_RECERT) can open the way a real
    admission note does -- "Admitted <name>... with terminal diagnosis of
    <dx> with comorbidities of <list>... referred to hospice with <MD>
    certifying... consents signed by <DPOA>" -- instead of reading like a
    routine follow-up visit.

    Only ever includes facts actually resolved from real records; a field
    that can't be found is simply omitted (never fabricated, never a
    placeholder like "Unknown"). Returns "" for non-admission assessment
    types (RN_RECERT and anything else) or on any failure -- never raises,
    always safe to call best-effort.
    """
    normalized_type = (assessment_type or "").upper()
    if normalized_type != "RNICA":
        # Only the admission assessment gets admission framing -- a
        # recertification visit is NOT an admission and must not be
        # narrated as one.
        return ""
    try:
        from app.models.certification import Certification
        from app.models.patient import Patient
        from app.models.patient_contact import PatientContact
        from app.models.patient_diagnosis import PatientDiagnosis
        from app.models.patient_facesheet import PatientFaceSheet
        from app.models.rnica_assessment import RnicaAssessment
        from app.models.user import User

        facesheet = (
            db.query(PatientFaceSheet).filter(PatientFaceSheet.patient_id == patient_id).one_or_none()
        )
        patient = db.query(Patient).filter(Patient.id == patient_id).one_or_none()

        lines: list[str] = []

        full_name = ""
        if facesheet:
            name_parts = [facesheet.first_name, facesheet.middle_name, facesheet.last_name]
            full_name = " ".join(p.strip() for p in name_parts if p and p.strip())
        if full_name:
            lines.append(f"- Patient full name: {full_name}")
        if facesheet and facesheet.dob:
            lines.append(f"- Date of birth: {facesheet.dob.isoformat()}")

        # Primary diagnosis: prefer the structured PatientDiagnosis(type=PRIMARY)
        # record; fall back to the plain Patient.primary_diagnosis string.
        primary_dx_row = (
            db.query(PatientDiagnosis)
            .filter(PatientDiagnosis.patient_id == patient_id, PatientDiagnosis.diagnosis_type == "PRIMARY")
            .order_by(PatientDiagnosis.created_at.desc())
            .first()
        )
        primary_dx = ""
        if primary_dx_row:
            primary_dx = primary_dx_row.display_name or primary_dx_row.diagnosis_description or ""
        if not primary_dx and patient and patient.primary_diagnosis:
            primary_dx = patient.primary_diagnosis
        if primary_dx:
            lines.append(f"- Primary/terminal diagnosis: {primary_dx}")

        # Secondary diagnoses / comorbidities: structured PatientDiagnosis
        # rows first, falling back to the RNICA form_data lists (same
        # flattening rules used elsewhere in the app for these two keys).
        secondary_rows = (
            db.query(PatientDiagnosis)
            .filter(
                PatientDiagnosis.patient_id == patient_id,
                PatientDiagnosis.diagnosis_type.in_(["SECONDARY", "COMORBIDITY"]),
            )
            .order_by(PatientDiagnosis.created_at.desc())
            .limit(10)
            .all()
        )
        comorbidities = [
            (row.display_name or row.diagnosis_description or "").strip()
            for row in secondary_rows
            if (row.display_name or row.diagnosis_description)
        ]
        if not comorbidities:
            assessment = (
                db.query(RnicaAssessment)
                .filter(RnicaAssessment.patient_id == patient_id, RnicaAssessment.assessment_type == "RNICA")
                .order_by(RnicaAssessment.created_at.desc())
                .first()
            )
            if assessment and isinstance(assessment.form_data, dict):
                diagnoses_section = assessment.form_data.get("diagnoses") or {}
                raw_list = list(diagnoses_section.get("secondaryDiagnoses") or []) + list(
                    diagnoses_section.get("comorbidities") or []
                )
                for item in raw_list:
                    if isinstance(item, str) and item.strip():
                        comorbidities.append(item.strip())
                    elif isinstance(item, dict):
                        text = (item.get("description") or item.get("name") or item.get("label") or "").strip()
                        if text:
                            comorbidities.append(text)
        comorbidities = [c for c in dict.fromkeys(comorbidities) if c][:8]
        if comorbidities:
            lines.append(f"- Comorbidities: {', '.join(comorbidities)}")

        # Decision maker / DPOA: PatientContact role first, facesheet
        # responsible-party name as fallback.
        decision_maker_contact = (
            db.query(PatientContact)
            .filter(
                PatientContact.patient_id == patient_id,
                PatientContact.role.in_(["DPOA", "DECISION_MAKER", "HEALTHCARE_AGENT"]),
            )
            .order_by(PatientContact.created_at.desc())
            .first()
        )
        decision_maker = ""
        if decision_maker_contact and decision_maker_contact.name:
            role_label = (decision_maker_contact.role or "").replace("_", " ").title()
            decision_maker = f"{decision_maker_contact.name} ({role_label})"
        elif facesheet and facesheet.responsible_party_name:
            decision_maker = facesheet.responsible_party_name
        if decision_maker:
            lines.append(f"- Decision maker / DPOA who signed consent: {decision_maker}")

        # Certifying/admitting MD: initial Certification.signed_by_user_id
        # first (most authoritative -- the physician who actually certified
        # the terminal prognosis), falling back to facesheet attending/
        # medical director name fields.
        certifying_md = ""
        cert_row = (
            db.query(Certification)
            .filter(Certification.patient_id == patient_id, Certification.cert_type == "INITIAL")
            .order_by(Certification.created_at.desc())
            .first()
        )
        if cert_row and cert_row.signed_by_user_id:
            user = db.query(User).filter(User.id == cert_row.signed_by_user_id).one_or_none()
            if user:
                certifying_md = getattr(user, "full_name", None) or " ".join(
                    p for p in [getattr(user, "first_name", None), getattr(user, "last_name", None)] if p
                )
        if not certifying_md and facesheet:
            certifying_md = facesheet.attending_physician_name or facesheet.medical_director_name or ""
        if certifying_md:
            lines.append(f"- Certifying/admitting physician: {certifying_md}")

        if not lines:
            return ""
        return "\n".join(lines)
    except Exception:
        logger.exception("note_draft_service: failed to build admission narrative context")
        return ""


def build_harvested_findings_context(db: Any, patient_id: Any, *, limit: int = 60) -> str:
    """Build a compact bullet list of this patient's already-harvested clinical
    findings (from previously uploaded documents such as the intake H&P) for
    use as `harvested_context` in `generate_note_draft`.

    Most of a hospice patient's durable clinical evidence comes from the H&P,
    not from any single visit -- this lets the voice-recording draft build on
    that record instead of ignoring it. Excludes DISMISSED signals (explicit
    clinician rejection); everything else (NEW/PENDING_REVIEW/ACKNOWLEDGED/
    ESCALATED) is still valid clinical context. Never raises -- returns ""
    on any failure so this is always safe to call best-effort.
    """
    try:
        from app.models.patient_evidence import PatientHarvestedSignal

        rows = (
            db.query(
                PatientHarvestedSignal.clinical_system,
                PatientHarvestedSignal.signal_text,
                PatientHarvestedSignal.original_text_excerpt,
                PatientHarvestedSignal.source_type,
                PatientHarvestedSignal.confidence,
            )
            .filter(
                PatientHarvestedSignal.patient_id == patient_id,
                PatientHarvestedSignal.review_status != "DISMISSED",
            )
            .order_by(PatientHarvestedSignal.recorded_at.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return ""
        lines = []
        seen: set[str] = set()
        for clinical_system, signal_text, original_text_excerpt, source_type, confidence in rows:
            text = (signal_text or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            prefix = f"[{clinical_system}] " if clinical_system else ""
            # Include the original quote + source so the model can attribute
            # findings precisely (e.g. `per H&P: "..."`) instead of writing
            # generic unsourced statements -- the DB already carries this
            # provenance, it just wasn't being forwarded before.
            source_label = "uploaded document" if source_type == "DOCUMENT_UPLOAD" else (source_type or "prior record")
            excerpt = (original_text_excerpt or "").strip()
            quote_part = f' -- quote: "{excerpt[:280]}"' if excerpt else ""
            confidence_part = f" (confidence {round(float(confidence) * 100)}%)" if confidence is not None else ""
            lines.append(f"- {prefix}{text} [source: {source_label}{confidence_part}]{quote_part}")
        return "\n".join(lines)
    except Exception:
        logger.exception("note_draft_service: failed to build harvested findings context")
        return ""
