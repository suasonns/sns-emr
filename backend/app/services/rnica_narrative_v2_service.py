"""RNICA Finalization Narrative -- v2 ("continuous RN narrative" structure).

This is a PREVIEW-ONLY generator: it reads the assessment's real structured
fields, real harvested evidence, real diagnoses/comorbidities, and real
medications, and composes a continuous Initial Comprehensive Assessment
narrative for RN review, written in the voice of a hospice RN admission
note rather than an AI-generated clinical/audit report. It never writes to
the assessment. The RN decides whether to copy any of the generated text
into diagnoses.clinicalNarrative (the one narrative field that is
quality-gated and reviewed -- see clinicalNarrativeBuilder.js).

The opening admission-context paragraph and the closing quick-reference
(terminal diagnosis/level of care/performance scales/code status) and
plan-of-care pointer are assembled deterministically from documented
fields only -- never invented, matching the same philosophy as
buildClinicalNarrative() in the frontend. The body of the narrative
(functional status and decline, body-system assessment findings in RN
workflow order, symptom burden, nutrition/elimination, safety/skin,
psychosocial/caregiver situation, interventions with teaching woven in
inline, and the clinical picture supporting continued hospice
appropriateness) is ONE grounded AI composition call over the same
evidence, required to narrate rather than list facts, to read like real
hospice-chart prose (no visible AI-report section banners -- see
strip_section_headers()), and to make no eligibility/certification/
prognosis/discharge determination.
"""


from __future__ import annotations

import re
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.rnica_assessment import RnicaAssessment
from app.services.evidence_center_service import _diagnoses, _medications, _numbered_evidence
from app.services.evidence.note_draft_service import _azure_openai_config
from app.services.rnica_intelligence import build_hospice_reasoning_panel
from app.services.scale_interpretations import format_scale_with_meaning, get_scale_interpretation

# Document-type labels and per-type voice guidance -- keyed off
# RnicaAssessment.assessment_type ("RNICA" / "UPDATE" / "RECERT", see
# app/api/visits.py's RNICA_ADMISSION_TYPE/RNICA_UPDATE_TYPE/
# RNICA_RECERT_TYPE). This is the actual document-type signal (it drives
# real admission-episode business rules elsewhere in the codebase), and
# it -- along with the RN-entered formData.visitMeta.reasonForVisit free
# text -- was previously never passed to the narrative model at all, so
# every visit type produced the same "admission" narrative regardless of
# whether this was an initial assessment, a routine follow-up, or a
# recertification. Both are now threaded into the system prompt (voice/
# opening/sequencing) and the evidence block (as verified context) below.
_ASSESSMENT_TYPE_LABELS: dict[str, str] = {
    "RNICA": "RN Initial Comprehensive Assessment",
    "UPDATE": "RN Follow-up / Routine Skilled Nursing Visit",
    "RECERT": "RN Recertification Assessment",
    "PRN": "RN PRN (unscheduled, problem-focused) Visit",
    "DEATH": "RN Death Visit / Pronouncement Note",
}

_ASSESSMENT_TYPE_VOICE: dict[str, str] = {
    "RNICA": (
        "This is an Initial Comprehensive Assessment -- the patient's FIRST hospice visit. Write "
        "it as a first encounter: open with why hospice is being elected now (terminal diagnosis, "
        "major contributing comorbidities, recent hospitalization if any, living situation, "
        "decision maker, code status) -- never assume the reader already knows this patient. "
        "Every finding should read as being seen for the first time today, and every piece of "
        "teaching and every intervention should read as being given/started for the first time, "
        "not reinforced or continued from a prior visit. Close with the initial plan of care "
        "being established."
    ),
    "RECERT": (
        "This is a Recertification Assessment -- the patient is already established on hospice "
        "service, and this visit documents continued decline for an additional benefit period. "
        "Write it as a continued-care visit, never an admission: open with the patient's CURRENT "
        "status and what has changed or declined since the last certification period -- never "
        "\"was admitted to hospice with...\" framing, since the patient is already on service. "
        "Emphasize continued/ongoing decline and continued dependence, and describe teaching and "
        "interventions as reinforcement of what the family/caregivers already know, not first-"
        "time introduction. Close with the continued plan of care."
    ),
    "UPDATE": (
        "This is a Follow-up / Routine Skilled Nursing Visit for a patient already established "
        "on hospice service -- not an admission and not a recertification. Write it as a routine "
        "check-in: open with today's visit findings and how they compare to the patient's known "
        "baseline, not \"was admitted to hospice\" framing. Emphasize what has changed or stayed "
        "the same since the last visit, ongoing symptom management, and reinforcement (not "
        "first-time teaching) of the existing plan of care."
    ),
    "PRN": (
        "This is an unscheduled, problem-focused PRN visit -- the RN was called out for ONE "
        "specific acute problem (e.g. uncontrolled pain, a fall, acute breathing crisis, a "
        "caregiver emergency), not a comprehensive head-to-toe reassessment. Open with what "
        "prompted the visit (who called, and why, and when) and keep the entire note tightly "
        "focused on that problem: your focused exam of the specific complaint, the specific "
        "intervention given, the response to that intervention, and instructions left with the "
        "caregiver for that problem. Do NOT restate the full admission history, do NOT walk "
        "through every body system, and do NOT re-document unrelated baseline findings that "
        "were not part of why this visit happened today. This note should read distinctly "
        "shorter and narrower in scope than a comprehensive assessment."
    ),
    "DEATH": (
        "This is a Death Visit / Pronouncement note -- the patient has died and this is an "
        "entirely different KIND of document, not a clinical status update. Do NOT discuss "
        "functional decline, performance scales (PPS/KPS/FAST/NYHA/ECOG), ongoing symptom "
        "management, or plan of care as if the patient were still living. Instead document, in "
        "plain narrative prose: the date/time the RN was called and arrived, who was present, "
        "the physical findings on pronouncement (absence of pulse/respirations/heart sounds, "
        "fixed pupils, etc.), the time of death and by whom/how it was determined, notification "
        "of the physician/medical director and family/next of kin, the family's and caregivers' "
        "reaction and any emotional support provided, notification and coordination with the "
        "funeral home and release of the body, disposition of controlled substances/medications "
        "and durable medical equipment, and initiation of bereavement services/follow-up. This "
        "note is fundamentally about the events immediately surrounding and after death, not "
        "about the patient's condition leading up to it."
    ),
}

_ASSESSMENT_TYPE_FLOW: dict[str, str] = {
    "RNICA": (
        "- Admission circumstances and why hospice was elected now, including terminal "
        "diagnosis, major contributing comorbidities, recent hospitalization if any, living "
        "situation, decision maker, and code status.\n"
        "- Initial functional baseline and dependence, with performance scales (PPS, KPS, FAST, "
        "NYHA, ECOG) woven directly into the descriptive sentences, never announced as a "
        "labeled scale, and always paired with its clinical meaning -- never a bare score.\n"
        "- Initial assessment findings in the order an RN actually works through a first visit "
        "-- neurological, respiratory, cardiovascular, pain, GI/GU, skin, musculoskeletal/"
        "safety -- narrated as plain observations establishing the baseline, not as labeled "
        "categories.\n"
        "- Initial nursing interventions and initial caregiver teaching folded in immediately "
        "next to the finding that prompted them, framed as being given for the first time. "
        "Include at least one or two things the RN physically did herself during the visit "
        "(e.g. repositioned him for comfort, offloaded a heel, applied a barrier product, "
        "administered a PRN medication if evidence supports it) -- not only things she told "
        "staff to do; a first visit is not only teaching, it is also hands-on care. Scope-of-"
        "practice note: routine musculoskeletal care -- passive range-of-motion stretching, "
        "massage, and scheduled repositioning -- is typically performed by the LVN/CHHA, not "
        "the RN. Do not write that the RN herself stretched or massaged the patient as routine "
        "care. Instead document the RN's own role -- assessing range of motion, stiffness, and "
        "positioning needs -- and then instructing/delegating: \"I instructed the LVN/CHHA to "
        "provide passive range-of-motion, massage, and repositioning every two hours as part of "
        "the plan of care.\" That instruction belongs in the plan-of-care content near the "
        "close, not attributed as the RN's own hands-on action. (In-the-moment comfort actions "
        "the RN performs herself during the visit itself, like offloading a heel or supporting "
        "a painful limb while assessing it, are still fine to document as the RN's own action.)\n"
        "- Caregiver and psychosocial context woven into the story wherever it naturally arose, "
        "including an explicit judgment of caregiver capability -- state whether staff/family "
        "demonstrated understanding of what was taught, asked appropriate questions, or will "
        "need closer follow-up/repetition (e.g. \"staff verbalized understanding and "
        "demonstrated correct use of the comfort kit,\" or \"caregiver will need reinforcement "
        "of the bowel regimen on the next visit\") -- never leave caregiver capability unstated.\n"
        "- The initial plan of care and hospice instructions, in plain nursing language, near "
        "the close, including any LVN/CHHA delegation such as scheduled ROM/repositioning."
    ),
    "RECERT": (
        "- Current status opening: the patient remains on hospice service, in what setting, "
        "with what terminal diagnosis, and what has changed or declined since the last "
        "certification period -- never admission-style framing.\n"
        "- Continued functional trajectory and dependence, with performance scales (PPS, KPS, "
        "FAST, NYHA, ECOG) woven in with their clinical meaning, explicitly framed as decline or "
        "trend since the last certification (e.g. \"continues to decline,\" \"remains,\" "
        "\"has progressively lost...\") rather than as a first-time finding.\n"
        "- Current assessment findings -- neurological, respiratory, cardiovascular, pain, "
        "GI/GU, skin, musculoskeletal/safety -- narrated as continued/trending observations.\n"
        "- Interventions and caregiver teaching described as reinforcement/continuation, folded "
        "in next to the finding that prompted them.\n"
        "- Caregiver and psychosocial context as it currently stands.\n"
        "- The continued plan of care and current goals, near the close."
    ),
    "UPDATE": (
        "- Opening with today's visit findings compared to the patient's known baseline -- not "
        "admission framing.\n"
        "- What has changed or stayed the same since the last visit, including functional status "
        "and any performance scale re-scored today, woven in with clinical meaning.\n"
        "- Current assessment findings relevant to today's visit -- narrated as plain "
        "observations, not a full re-derivation of the original admission history.\n"
        "- Ongoing interventions and reinforcement (not first-time) teaching folded in next to "
        "the finding that prompted them.\n"
        "- Caregiver/psychosocial context as it stands today.\n"
        "- Reinforcement of the ongoing plan of care near the close."
    ),
    "PRN": (
        "- What prompted this visit -- who called, when, and why -- stated up front.\n"
        "- The focused exam/findings specific to that one problem only.\n"
        "- The specific intervention given and the patient's response to it.\n"
        "- Instructions left with the caregiver/family specific to this problem.\n"
        "- A brief closing statement of the plan for follow-up on this specific issue -- do not "
        "re-document the full comprehensive plan of care."
    ),
    "DEATH": (
        "- When the RN was called, when the RN arrived, and who was present in the home/"
        "facility.\n"
        "- Physical findings on pronouncement and how/when death was determined.\n"
        "- Notification of the physician/medical director and of family/next of kin, and their "
        "reaction.\n"
        "- Emotional support provided to family/caregivers at the bedside.\n"
        "- Funeral home notification/coordination and release of the body.\n"
        "- Disposition of controlled substances, medications, and durable medical equipment.\n"
        "- Initiation of bereavement services/follow-up, near the close."
    ),
}


def _build_system_prompt(assessment_type_code: str, reason_for_visit: str) -> str:
    document_type_label = _ASSESSMENT_TYPE_LABELS.get(assessment_type_code, "RN Assessment")
    voice_guidance = _ASSESSMENT_TYPE_VOICE.get(assessment_type_code, _ASSESSMENT_TYPE_VOICE["RNICA"])
    flow_guidance = _ASSESSMENT_TYPE_FLOW.get(assessment_type_code, _ASSESSMENT_TYPE_FLOW["RNICA"])
    reason_line = (
        f' The RN-documented reason for this specific visit is "{reason_for_visit}" -- let it '
        f"further refine tone (for example a bereavement-support or crisis-intervention reason "
        f"should read differently than a routine decline check-in) without contradicting the "
        f"document-type guidance above."
        if reason_for_visit
        else ""
    )
    return f"""You are an experienced hospice RN dictating a {document_type_label} narrative \
immediately after finishing a home visit -- NOT a diagnosis, NOT a certification, NOT a \
prognosis determination, and NOT a compliance/audit review.

ASSESSMENT CONTEXT (this determines the narrative's opening, sequencing, and emphasis -- a \
nurse reading the finished note should immediately recognize what kind of visit this was \
purely from how it is written, never from a literal label or banner stating the document \
type): {voice_guidance}{reason_line}

Write ONE continuous narrative, the way a real hospice RN dictates a note right after a \
visit. Do NOT structure it as a series of topic blocks (even without visible headers -- the \
underlying block structure itself must not be detectable). Move through the visit the way \
it actually happened: weave what you observed, what it means, and what you did together in \
the same breath, rather than saving every intervention and every piece of teaching for a \
separate place at the end.

Loose narrative flow for THIS document type to move through (blend continuously -- these are \
NOT section breaks and must never be visually or structurally separated from each other; do \
NOT use the flow for a different document type than the ASSESSMENT CONTEXT above specifies):
{flow_guidance}
- Performance-scale rule (applies only when the flow above calls for functional status, i.e. \
NOT for a PRN or Death visit unless directly relevant to why the visit happened): scales must \
always be paired with their clinical meaning -- never a bare score. Write "Patient remains \
bedbound with PPS 40%, indicating he is mainly in bed and requires assistance for most \
activity, and KPS 40, reflecting his need for special care," never "Performance scales \
include PPS 40%, KPS 40%" and never "PPS 40%" alone with no explanation of what that means. \
Write "Patient demonstrates NYHA Class IV heart failure, with symptoms present even at rest \
and inability to tolerate any physical activity without discomfort," never "Disease-specific \
scale: NYHA IV" and never "NYHA IV" alone. The same rule applies to FAST and ECOG: always \
state what the stage/grade means in plain language in the same sentence the score appears, \
using the meaning given in the verified-facts block below -- never invent a meaning not \
given there. Never invent a scale left blank.

NEVER NAME THE DOCUMENT TYPE OR VISIT REASON DIRECTLY. Do not write phrases like "initial \
comprehensive assessment," "comprehensive assessment visit," "routine follow-up visit," \
"recertification visit," "PRN visit," or "pronouncement and discharge/transfer visit" \
anywhere in the narrative -- these are metadata labels, not clinical observations, and a \
real hospice RN dictating a note never states the name of the document she is filling out. \
The visit type must be revealed ONLY through what actually gets described and in what depth \
-- an admission story with decision-maker/living-situation introduction and first-time \
teaching for an initial assessment; decline-since-last-certification framing for a \
recertification; a tightly scoped single-problem story for a PRN call; pronouncement/family-\
notification/funeral-home content for a death visit -- never through a sentence that simply \
announces which of these this is. If you notice yourself writing "for" followed by the name \
of a visit type ("visit for an initial comprehensive assessment," "visit for a PRN," "visit \
for recertification"), delete that phrase and describe the actual event instead (why the RN \
came out today, what was found, what was done).

VOICE -- the single biggest quality bar: this must read like a real hospice RN wrote it, \
never like an AI clinical report, audit summary, utilization-review note, or medical- \
necessity analysis. Before you finish, silently ask yourself: "would an experienced hospice \
RN believe another hospice RN wrote this?" and "what phrases here would immediately reveal \
this was AI-written?" -- then rewrite anything that would.

BE OBSERVATIONAL, NOT EXPLANATORY. A real RN documents what she saw and did. An AI report \
summarizes and interprets what it read. Never write a sentence whose job is to summarize, \
characterize, or draw a conclusion about the findings you just gave -- state the finding \
itself and stop. Do not write summarizing/interpretive sentences such as "these changes \
describe advanced functional decline," "this reflects a heavy symptom burden," "this \
represents significant dependence," "collectively these findings indicate...," or "the \
patient's clinical picture is one of decline." Instead, simply document the observation \
directly: "Patient remains bedbound and dependent for all ADLs," "Patient continues to \
complain of pain and shortness of breath," "Patient requires total assistance with \
repositioning and hygiene." If you notice yourself writing "this shows," "this reflects," \
"this indicates," "this represents," "these changes," "these findings," or "overall, the \
patient" -- delete the sentence and replace it with the plain observation it was trying to \
summarize.

THE RN MUST BE THE VISIBLE ACTOR, NOT A HIDDEN ONE. This is the difference between an RN \
assessment and a patient summary: a summary reports what is true about the patient; an \
assessment documents what the nurse herself observed, assessed, reviewed, educated, \
instructed, performed, discussed, established, and planned during the visit. Every \
sentence describing something the RN did -- reviewing a medication list, starting teaching, \
inspecting skin, discussing a plan, instructing a caregiver, establishing a plan of care -- \
must have the RN as the grammatical subject ("I reviewed...", "I instructed...", "I \
observed...", "I discussed...", "I established...", "I initiated teaching on...", "I \
assessed..."). NEVER bury the nurse's own action behind passive voice, as in "teaching was \
started," "medications were reviewed with staff," "consents were in place," "safety \
teaching was reinforced," "plan established today is for...", or "skin inspection showed." \
Rewrite every one of those into an active sentence naming the RN as the one who did it: "I \
started teaching on...", "I reviewed medications with staff...", "I confirmed consents were \
in place...", "I reinforced safety teaching...", "I established a plan for...", "I inspected \
the skin and found...". Reserve passive/third-person phrasing ONLY for things the RN did not \
personally do -- what the patient reports, what family/caregivers report, or an objective \
physical fact like a lab value or a wound stage that simply exists rather than being an \
action. A finished RNICA/UPDATE/RECERT/PRN narrative should contain many first-person \
sentences documenting the nurse's own assessment, teaching, and planning actions throughout \
-- not clustered in one paragraph -- so that a reader can trace the nurse's actual workflow \
during the visit, not just a list of facts about the patient. (Exception: a Death visit may \
still use first person for the RN's own pronouncement/notification/coordination actions -- \
"I contacted the funeral home," "I notified the attending" -- following the same rule.)

FOLLOW THE CLINICAL REASONING CHAIN, NOT JUST A LIST OF ELEMENTS. A real hospice RN note \
does not simply list finding, intervention, and teaching side by side -- it shows the chain: \
Finding -> what that finding meant clinically -> what the RN did about it -> how the patient/\
situation responded -> what was taught -> what the plan is. For at least every major system \
you assess in depth (not necessarily every minor one), close the loop by documenting an \
observable RESPONSE to whatever the RN did or gave, not just the action itself. Examples of \
closing the loop: "...and he appeared more comfortable after repositioning," "...tolerated \
the position change without increased shortness of breath," "...breathing eased somewhat \
after the head of the bed was raised," "...no new redness noted after offloading the heel," \
"...pain was less guarded on re-check before I left." If you document an intervention and \
never say what happened afterward, the reader cannot tell whether it worked -- go back and \
add the observed response. Do not manufacture a response that was not evidenced; if no \
recheck happened, it is acceptable to state that follow-up response will be assessed on the \
next visit rather than inventing one.

CAREGIVER CAPABILITY MUST BE A JUDGMENT, NOT JUST AN INTERACTION. Do not stop at documenting \
that a caregiver was present, asked questions, or verbalized understanding -- that only \
proves an interaction happened. Go further and state the RN's actual judgment: is the \
caregiver willing to provide the needed care, able to physically/cognitively perform it, \
competent in what was demonstrated today, actively participating in care during the visit, \
and -- most importantly -- can the plan be carried out safely with this caregiver in place, \
or does it need reinforcement, a different caregiver, or additional hospice support before \
the next visit? State that conclusion directly, e.g. "Caregivers demonstrated safe technique \
for repositioning and are able to carry out the pain regimen independently, though bowel \
regimen teaching will need reinforcement before the next visit," rather than only "caregivers \
verbalized understanding."

MAKE RN-PERFORMED ACTIONS SPECIFIC AND OBSERVABLE, NOT GENERIC. Prefer concrete, checkable \
actions over vague ones: "repositioned patient," "offloaded the right heel," "performed skin \
inspection at the coccyx and heel," "demonstrated use of the oxygen concentrator," "assessed \
pain response before and after medication," "reviewed the medication list against what is in \
the home" -- never a vague catch-all like "provided care" or "addressed concerns" with no \
specific, checkable action named. Scope-of-practice exception: routine passive range-of-\
motion stretching, massage, and scheduled repositioning are LVN/CHHA-level tasks, not RN \
tasks -- never write that the RN herself stretched, massaged, or performed routine range-of-\
motion exercises; instead document the RN's assessment of the need and her instruction/\
delegation of that task to the LVN/CHHA as part of the plan of care.

Never discuss hospice eligibility or appropriateness directly, and never write a sentence \
whose purpose is to argue eligibility. Do not write, in any form: "patient is appropriate \
for hospice", "meets criteria", "clinical picture", "clinical picture supports", "hospice \
appropriateness", "documentation supports", "eligibility support", "terminal prognosis \
support", "disease burden", "criteria support", "eligibility summary", "continued hospice \
appropriateness", or "patient remains appropriate". Simply document the facts -- decline, \
dependence, progression despite treatment, symptom burden, weight loss, caregiver burden -- \
and let the reader arrive at the conclusion of hospice appropriateness on their own, the way \
a real chart note never states its own legal conclusion.

Every claim must be grounded in the structured fields, harvested evidence, or medication list \
given below -- never invented.

Never make an eligibility, certification, prognosis, or discharge determination.

Also ban these words/phrases entirely, in any form: "data", "documented as", "recorded as", \
"identified as", "tracked as", "tracked against", "evidence references", "source", "field", \
"finding(s)" used as a noun for a data point, "structured", "assessment reveals/indicates" \
used repeatedly as a crutch, "these changes", "these findings", "this reflects", "this \
represents", "this indicates", "this describes", "collectively", "heavy symptom burden", \
"overall, the patient", "the patient's clinical picture is". Never write the clinical-abstraction-report voice of listing \
attributes; write the hospice-chart voice of describing a person. Center every sentence on \
the patient, not on the record -- write "the patient continues to experience...", "the \
patient's condition has progressed...", "the family reports...", "caregiver reports...", \
"teaching provided...", "wound care completed...", "comfort measures reinforced..." -- never \
"the chart shows...", "the assessment documents...", "the data indicates...".

A verified-facts block is provided below (terminal diagnosis and code, level of care, code \
status, any scored performance scales with their published clinical meaning). Unless the \
ASSESSMENT CONTEXT above is a Death visit (where functional/performance-scale detail is not \
relevant) or a PRN visit unrelated to functional status, every individual scale given -- PPS, \
KPS, FAST, NYHA, and ECOG, whichever are present -- MUST each appear by name, exact value, \
AND its given meaning somewhere in the narrative, woven into the functional-status passage. \
Do NOT drop a scale just because another scale already conveys similar functional \
information -- if both PPS and NYHA are given, both PPS and NYHA must each appear with their \
meaning; a disease-specific scale (NYHA for heart failure, ECOG for cancer, FAST for \
dementia) is exactly the detail a reviewer looks for and must never be silently omitted in \
favor of only the general PPS/KPS scales. State these facts where a real RN would naturally \
state them for this document type -- never fabricate a value or meaning not given, and never \
present this block itself as a separate labeled section.

Output ONE continuous block of plain narrative text. No headers, no bullet points, no JSON, \
no blank-line-separated topic blocks.
"""


def _call_azure_plain_text(system_prompt: str, user_content: str) -> str:
    config = _azure_openai_config()
    if config is None:
        raise RuntimeError("Azure OpenAI is not configured in this environment.")
    url = (
        f"{config['endpoint']}/openai/deployments/{config['deployment']}"
        f"/chat/completions?api-version={config['api_version']}"
    )
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
    }
    response = httpx.post(
        url,
        headers={"api-key": config["api_key"], "Content-Type": "application/json"},
        json=payload,
        timeout=90.0,
    )
    response.raise_for_status()
    body = response.json()
    return body["choices"][0]["message"]["content"]


def _safe(d: dict | None, *keys: str, default: Any = "") -> Any:
    cur = d or {}
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    return cur if cur not in (None, "") else default


def _ai_draft_evidence(db: Session, patient_id: UUID) -> list[dict[str, Any]]:
    """Concept-coded findings already extracted from this patient's visit-
    recording AI Draft (ai_note_draft.structured_findings) -- verbatim
    transcript quotes with a confidence score, not the draft's free-text
    narrative. Treated as EVIDENCE for grounding, never copied as output
    text, per the same contract as harvested signals."""
    rows = db.execute(
        text(
            "SELECT ai_note_draft FROM visit_recordings "
            "WHERE patient_id = :pid AND transcript_status = 'COMPLETED' "
            "AND ai_note_draft IS NOT NULL ORDER BY recorded_at"
        ),
        {"pid": str(patient_id)},
    ).fetchall()
    findings: list[dict[str, Any]] = []
    for row in rows:
        draft = row.ai_note_draft or {}
        for f in draft.get("structured_findings", []) or []:
            if f.get("assertion_status") == "UNCERTAIN":
                continue
            findings.append(
                {
                    "clinical_system": f.get("concept_code", "").split("_")[0].title(),
                    "fact": f"{f.get('concept_code')}={f.get('value')} (confidence {f.get('confidence')})",
                    "source_excerpt": f.get("source_excerpt"),
                    "source_type": "AI_DRAFT_STRUCTURED_FINDING",
                }
            )
    return findings


# ---------------------------------------------------------------------
# Clinical Documentation Gap Detection.
#
# Compares what is being DISCUSSED (harvested evidence + AI-Draft
# concept-coded structured findings, which already carry a source
# quote + confidence) against what is DOCUMENTED (structured RNICA
# fields). Purely rule-based cross-reference -- no additional AI call,
# no invented content, no eligibility/prognosis opinion. A gap is
# reported only when BOTH: (a) matching evidence exists, AND (b) the
# corresponding structured field(s) are genuinely blank. Never auto-
# fills the field; only prompts the RN with what to consider
# documenting and the evidence that suggested it.
# ---------------------------------------------------------------------
_GAP_RULES: list[dict[str, Any]] = [
    {
        "topic": "Functional Performance Scale (PPS/KPS/FAST/ECOG/NYHA)",
        "trigger_keywords": ["bedbound", "ambulat", "rom_loss", "hemipar", "mobility", "weak", "decline"],
        "check_blank": lambda fd: not any((fd.get("performanceStatus") or {}).values()),
        "message": "Evidence discusses functional decline (e.g. bedbound status, mobility loss), but no performance "
        "scale (PPS/KPS/FAST/ECOG/NYHA) is scored on this assessment. A scored scale converts this discussion "
        "into a documented severity tier (e.g. mild/moderate/severe/advanced functional decline) that a "
        "physician, surveyor, or auditor can act on -- without it, the decline described in the conversation "
        "has no corresponding structured, chartable evidence.",
        "suggested_fields": ["performanceStatus.pps", "performanceStatus.fast", "performanceStatus.kps"],
    },
    {
        "topic": "Activities of Daily Living (ADLs)",
        "trigger_keywords": ["bedbound", "transfer", "dependent", "assist", "rom_loss", "hemipar"],
        "check_blank": lambda fd: not any(((fd.get("musculoskeletal") or {}).get("adl") or {}).values()),
        "message": "Evidence discusses functional dependence, but ADL fields (eating/bathing/dressing/grooming/"
        "toileting/transferring) are blank.",
        "suggested_fields": ["musculoskeletal.adl.eating", "musculoskeletal.adl.transferring"],
    },
    {
        "topic": "Nutrition / Oral Intake",
        "trigger_keywords": ["appetite", "intake", "nutrition", "malnutrition", "eating half", "poor appetite"],
        "check_blank": lambda fd: not any((fd.get("nutrition") or {}).values()),
        "message": "Evidence discusses nutrition/appetite concerns, but nutrition fields are blank.",
        "suggested_fields": ["nutrition.weightLossPastSixMonths", "nutrition.dietType"],
    },
    {
        "topic": "Psychosocial / Caregiver Concerns",
        "trigger_keywords": ["caregiver", "brother", "family", "psych", "support", "distress", "concern"],
        "check_blank": lambda fd: not any((fd.get("psychosocial") or {}).values()),
        "message": "Evidence discusses caregiver/family context, but psychosocial fields (distress rating, patient "
        "concerns, family/social support) are blank.",
        "suggested_fields": ["psychosocial.distressRating", "psychosocial.familySocialSupport"],
    },
    {
        "topic": "Symptom Impact Screening",
        "trigger_keywords": ["pain_", "resp_", "gi_", "dyspnea", "constipation", "shortness of breath"],
        "check_blank": lambda fd: not any((fd.get("symptomImpact") or {}).values()),
        "message": "Evidence discusses symptom burden (pain/dyspnea/GI), but symptom impact screening fields "
        "are blank.",
        "suggested_fields": ["symptomImpact.pain", "symptomImpact.shortnessOfBreath", "symptomImpact.constipation"],
    },
    {
        "topic": "Skin / Wound Documentation",
        "trigger_keywords": ["skin_wound", "pressure", "ulcer", "wound"],
        "check_blank": lambda fd: not ((fd.get("skin") or {}).get("wounds")),
        "message": "Evidence discusses skin breakdown/pressure injury, but no wounds are documented in the "
        "structured skin assessment.",
        "suggested_fields": ["skin.wounds"],
    },
    {
        "topic": "Recent Hospitalizations / ER Utilization",
        "trigger_keywords": ["hospitaliz", "er visit", "emergency room", "admission", "readmit"],
        "check_blank": lambda fd: not (fd.get("diagnoses") or {}).get("recentErVisits")
        and not (fd.get("diagnoses") or {}).get("recentHospitalizations"),
        "message": "Evidence discusses hospitalization/ER utilization, but recent hospitalization/ER visit counts "
        "are not documented.",
        "suggested_fields": ["diagnoses.recentHospitalizations", "diagnoses.recentErVisits"],
    },
]


# ---------------------------------------------------------------------
# Documentation Conflict Detection.
#
# Distinct from a "gap" (evidence exists, structured field is blank):
# a conflict is evidence pointing to two or more mutually exclusive
# clinical states (e.g. "bedbound" AND "seen sitting on a couch"). The
# narrative must never silently pick one -- it is surfaced to the RN as
# a required confirmation, using the SAME Documentation Insights shape
# ("topic"/"message"/"suggested_fields"/"supporting_quotes") plus a
# "kind": "conflict" marker so the UI can prompt for RN confirmation
# rather than treat it as an optional documentation opportunity. This is
# intentionally a small, generic, keyword-group mechanism (not hardcoded
# to any one patient's chart) -- additional conflict sets can be added
# to _CONFLICT_RULES without new plumbing.
# ---------------------------------------------------------------------
_CONFLICT_RULES: list[dict[str, Any]] = [
    {
        "topic": "Mobility Status",
        "message": "The visit discussion and existing documentation describe more than one current mobility "
        "status for this patient (for example bedbound, chair/wheelchair-dependent, or able to sit up with "
        "assistance). Please confirm the patient's current mobility status before it is reflected in the "
        "narrative.",
        "suggested_fields": ["musculoskeletal.mobility.ambulatoryStatus", "performanceStatus.pps"],
        "groups": {
            "bedbound": ["bedbound", "bed-bound", "confined to bed"],
            "chair/wheelchair-dependent": ["chairbound", "chair-bound", "wheelchair dependent", "wheelchair-dependent"],
            "able to sit up / ambulate": ["sitting on a couch", "sitting up", "seen sitting", "ambulates", "ambulatory"],
        },
    },
]


def detect_documentation_conflicts(fd: dict[str, Any], evidence_facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts_found = []
    for rule in _CONFLICT_RULES:
        matched_groups: dict[str, list[str]] = {}
        for group_name, keywords in rule["groups"].items():
            for e in evidence_facts:
                haystack = " ".join(
                    str(e.get(k, "")) for k in ("fact", "clinical_system", "source_excerpt", "signal_key")
                ).lower()
                if any(kw in haystack for kw in keywords):
                    quote = e.get("source_excerpt")
                    if quote:
                        matched_groups.setdefault(group_name, [])
                        if quote not in matched_groups[group_name]:
                            matched_groups[group_name].append(quote)
        if len(matched_groups) >= 2:
            quotes: list[str] = []
            for group_quotes in matched_groups.values():
                for q in group_quotes:
                    if q not in quotes:
                        quotes.append(q)
                    if len(quotes) >= 4:
                        break
            conflicts_found.append(
                {
                    "kind": "conflict",
                    "topic": rule["topic"],
                    "message": rule["message"],
                    "suggested_fields": rule["suggested_fields"],
                    "supporting_quotes": quotes,
                    "conflicting_statuses": list(matched_groups.keys()),
                }
            )
    return conflicts_found


def detect_documentation_gaps(fd: dict[str, Any], evidence_facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps_found = []
    for rule in _GAP_RULES:
        if not rule["check_blank"](fd):
            continue
        matches = []
        for e in evidence_facts:
            haystack = " ".join(
                str(e.get(k, "")) for k in ("fact", "clinical_system", "source_excerpt", "signal_key")
            ).lower()
            if any(kw in haystack for kw in rule["trigger_keywords"]):
                if e.get("source_excerpt"):
                    matches.append(e["source_excerpt"])
        if matches:
            seen = []
            for m in matches:
                if m not in seen:
                    seen.append(m)
                if len(seen) >= 2:
                    break
            gaps_found.append(
                {
                    "topic": rule["topic"],
                    "message": rule["message"],
                    "suggested_fields": rule["suggested_fields"],
                    "supporting_quotes": seen,
                }
            )
    return gaps_found


def generate_rnica_narrative_v2(db: Session, assessment_id: UUID) -> dict[str, Any]:
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_id).first()
    if not record:
        raise ValueError("Assessment not found")

    fd = record.form_data or {}
    patient_id = record.patient_id
    hospice_reasoning = build_hospice_reasoning_panel(db, str(patient_id)) if patient_id else {}
    related = hospice_reasoning.get("related_conditions") or {}
    gaps = hospice_reasoning.get("documentation_gaps") or []

    # Assessment/document-type context (RNICA/UPDATE/RECERT + the RN's
    # documented reason for this visit) -- previously never read at all,
    # which meant every visit type produced an identical "initial
    # admission" narrative regardless of whether this was a first visit,
    # a routine follow-up, or a recertification.
    assessment_type_code = (record.assessment_type or "RNICA").upper()
    visit_meta = fd.get("visitMeta") or {}
    reason_for_visit = str(visit_meta.get("reasonForVisit") or "").strip()
    document_type_label = _ASSESSMENT_TYPE_LABELS.get(assessment_type_code, "RN Assessment")

    harvested = _numbered_evidence(db, patient_id) if patient_id else []
    medications = _medications(db, patient_id) if patient_id else []

    demo = fd.get("demographics", {}) or {}
    dx = fd.get("diagnoses", {}) or {}
    primary_dx = dx.get("primaryDiagnosis", {}) or {}
    pcg = demo.get("pcg", {}) or {}
    musculo = fd.get("musculoskeletal", {}) or {}
    symptom = fd.get("symptomImpact", {}) or {}
    resp = fd.get("respiratory", {}) or {}
    nutrition = fd.get("nutrition", {}) or {}
    skin = fd.get("skin", {}) or {}
    psychosocial = fd.get("psychosocial", {}) or {}

    # --- Verified facts (deterministic, never invented): terminal
    # diagnosis + code, comorbidities, level of care, code status, scored
    # performance scales. These are NOT concatenated onto the narrative as
    # separate stitched paragraphs -- the whole point of this rewrite is
    # that the RN-facing text must be ONE continuous AI-generated
    # narrative, not an assembly of deterministic + AI blocks (which still
    # reads as "AI report architecture" even with headers removed). They
    # are instead handed to the model as grounding facts it must weave
    # naturally into its own narrative (see SYSTEM_PROMPT's "verified-facts
    # block" instruction), and kept here only for API-shape backward
    # compatibility (section1/section9/section10 fields) and as a safety
    # net (see fallback below) if the model ever omits the diagnosis.
    name = f"{demo.get('firstName', '')} {demo.get('lastName', '')}".strip() or "Patient"
    gender = demo.get("gender", "")
    comorbidities = [c.get("description") for c in related.get("related", []) if c.get("description")]
    dx_description = primary_dx.get("description") or "to be confirmed"
    section1 = (
        f"{name}{f', {gender.lower()},' if gender else ''} was admitted to hospice with a terminal "
        f"diagnosis of {dx_description}."
        + (f" Comorbidities include {', '.join(comorbidities)}." if comorbidities else "")
    )

    perf = fd.get("performanceStatus") or {}
    level_of_care = ((fd.get("admissionsOrder") or {}).get("levelOfCare") or {}).get("level")
    code_status = (fd.get("advancedCarePlanning") or {}).get("codeStatus")
    dx_code = primary_dx.get("code")
    summary_bits = [f"Terminal diagnosis: {dx_description}"]
    if dx_code:
        summary_bits[-1] += f" ({dx_code})"
    if level_of_care:
        summary_bits.append(f"Level of care: {level_of_care}")
    for label, key in (("PPS", "pps"), ("KPS", "kps"), ("FAST", "fast"), ("NYHA", "nyha"), ("ECOG", "ecog")):
        if perf.get(key):
            # Include the published clinical meaning alongside the raw
            # score -- a bare "NYHA IV" or "PPS 40%" is meaningless to
            # most readers; the interpretation is what a physician,
            # surveyor, or family member actually needs (per explicit
            # requirement that scores must never appear without meaning).
            meaning = format_scale_with_meaning(key, perf.get(key))
            summary_bits.append(meaning if meaning else f"{label}: {perf.get(key)}")
    if code_status:
        summary_bits.append(f"Code status: {code_status}")
    section9 = ". ".join(summary_bits) + "."

    section10 = "Plan of care: see current Plan of Care for active problems, goals, and interventions."

    # --- Grounding evidence block for the single narrative-generation call ---
    ai_draft_findings = _ai_draft_evidence(db, patient_id) if patient_id else []
    evidence_lines = []
    n = 0
    for e in harvested:
        n += 1
        quote = f' -- quote: "{e["source_excerpt"]}"' if e.get("source_excerpt") else ""
        evidence_lines.append(f"{n}. [{e['clinical_system'] or 'general'}] {e['fact']}{quote}")
    for f in ai_draft_findings:
        n += 1
        quote = f' -- quote: "{f["source_excerpt"]}"' if f.get("source_excerpt") else ""
        evidence_lines.append(f"{n}. [AI Draft / {f['clinical_system'] or 'general'}] {f['fact']}{quote}")

    scale_grounding_lines = []
    for label, key in (("PPS", "pps"), ("KPS", "kps"), ("FAST", "fast"), ("NYHA", "nyha"), ("ECOG", "ecog")):
        value = perf.get(key)
        if not value:
            continue
        meaning = format_scale_with_meaning(key, value)
        scale_grounding_lines.append(meaning if meaning else f"{label}: {value}")

    structured_lines = [
        "PPS/KPS/FAST/ECOG/NYHA: "
        + ("; ".join(scale_grounding_lines) if scale_grounding_lines else "all blank -- not documented in structured fields."),
        f"Ambulatory status: {_safe(musculo, 'mobility', 'ambulatoryStatus', default='not documented')}.",
        f"Paralysis: {_safe(musculo, 'paralysis', default='not documented')}.",
        f"ROM limitations: {musculo.get('romLimitations') or 'none documented'}.",
        f"Symptom impact screening: pain={symptom.get('pain')}, SOB={symptom.get('shortnessOfBreath')}, "
        f"constipation={symptom.get('constipation')} (0=none,3=severe).",
        f"Respiratory: SOB severity '{_safe(resp, 'sobSeverity', default='not documented')}', "
        f"exertion level '{_safe(resp, 'exertionLevel', default='not documented')}'.",
        f"Nutrition: weight loss '{_safe(nutrition, 'weightLossPastSixMonths', default='not documented')}', "
        f"diet type '{_safe(nutrition, 'dietType', default='not documented')}', "
        f"supplement '{_safe(nutrition, 'nutritionalSupplements', default='not documented')}'.",
        f"Skin: wounds documented at {[w.get('location') for w in skin.get('wounds', [])] or 'none documented'}, "
        f"stages: {[w.get('stage') for w in skin.get('wounds', []) if w.get('stage')] or 'none documented'}.",
        f"Psychosocial: distress rating {psychosocial.get('distressRating')}, "
        f"concerns {psychosocial.get('patientConcerns') or 'none documented'}, "
        f"family/social support '{_safe(psychosocial, 'familySocialSupport', default='not documented')}', "
        f"primary support person: {_safe(psychosocial, 'primarySupportPerson', default='not documented')}.",
        f"Caregiver availability: {_safe(pcg, 'caregiverEvaluation', 'availabilityForCare', default='not documented')}.",
        "Documentation gaps for certification support (still needed): "
        + ("; ".join(g.get("gap", "") for g in gaps) if gaps else "none outstanding."),
    ]

    med_lines = [
        f"{m['medication_name']} {m['dosage']} {m['route']} {m['frequency']} "
        f"({'PRN' if m['is_prn'] else 'scheduled'})"
        for m in medications
    ]

    evidence_block = (
        "--- ASSESSMENT CONTEXT (document type -- drives narrative voice/opening/sequencing per "
        "the system prompt; never state this as a literal label in the output) ---\n"
        f"Document type: {document_type_label}.\n"
        f"Reason for visit: {reason_for_visit or 'not documented'}.\n"
        + "\n--- VERIFIED FACTS (weave naturally into the narrative; never fabricate a value not "
        "given here) ---\n" + f"Patient name: {name}{f', {gender}' if gender else ''}.\n" + section9
        + "\n\n--- STRUCTURED RNICA FIELDS ---\n" + "\n".join(structured_lines)
        + "\n\n--- NUMBERED EVIDENCE (harvested findings + AI-Draft-extracted structured findings from visit recordings; use as grounding only, never quote the AI Draft's own prose) ---\n" + "\n".join(evidence_lines)
        + "\n\n--- CURRENT MEDICATIONS ---\n" + "\n".join(med_lines)
    )

    # --- Clinical Documentation Gap Detection: what is discussed in the
    # evidence but not yet reflected in structured RNICA fields. Purely
    # rule-based, computed regardless of whether the AI call below runs. ---
    all_evidence = harvested + ai_draft_findings
    documentation_gaps_detected = detect_documentation_gaps(fd, all_evidence)
    documentation_conflicts_detected = detect_documentation_conflicts(fd, all_evidence)

    # Structured clinical evidence per scale -- see full definition below
    # where it's returned; computed here too so it is present even when no
    # AI call runs (config not set), since it's derived purely from
    # structured data, not from the AI narrative.
    scale_clinical_evidence = []
    for label, key in (("PPS", "pps"), ("KPS", "kps"), ("FAST", "fast"), ("NYHA", "nyha"), ("ECOG", "ecog")):
        value = perf.get(key)
        if not value:
            continue
        interp = get_scale_interpretation(key, value)
        if interp:
            scale_clinical_evidence.append(interp)

    config = _azure_openai_config()
    if config is None:
        return {
            "ai_configured": False,
            "section1": section1,
            "section9": section9,
            "section10": section10,
            "middle_sections": None,
            "full_text": None,
            "documentation_gaps_detected": documentation_gaps_detected,
            "documentation_conflicts_detected": documentation_conflicts_detected,
            "lcd_support_section": None,
            "scale_clinical_evidence": scale_clinical_evidence,
        }

    system_prompt = _build_system_prompt(assessment_type_code, reason_for_visit)
    full_text = _call_azure_plain_text(system_prompt, evidence_block).strip()

    # Safety net only -- the prompt already requires the diagnosis to be
    # woven in naturally, and it is expected (and fine) for the model to
    # paraphrase/reorder it (e.g. "chronic systolic heart failure" instead
    # of "SYSTOLIC HEART FAILURE, CHRONIC"), so this checks for meaningful
    # word overlap rather than an exact substring -- an exact-phrase check
    # would false-positive on ordinary paraphrasing and reintroduce exactly
    # the kind of trailing AI-report artifact this rewrite removes.
    def _dx_words(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}

    dx_word_set = _dx_words(dx_description) if dx_description else set()
    if dx_word_set and assessment_type_code != "DEATH":
        overlap = dx_word_set & _dx_words(full_text)
        if len(overlap) < max(1, int(len(dx_word_set) * 0.6)):
            full_text = f"{full_text}\n\n{section9}"

    # Per-scale safety net: the prompt requires every provided scale (PPS,
    # KPS, FAST, NYHA, ECOG) to individually appear WITH its clinical
    # meaning, not just the bare score -- a bare "NYHA IV" is meaningless
    # to most readers. Models sometimes weave in only the raw score, or
    # weave in only the general scales (PPS/KPS) and silently drop a
    # disease-specific one (e.g. NYHA for a CHF patient). Check each scale
    # present in structured data for both (a) the score itself and (b) its
    # published meaning appearing in the output; append one plain sentence
    # (never a labeled block) for whichever is missing.
    def _meaning_words(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3}

    missing_scale_sentences = []
    if assessment_type_code not in ("DEATH", "PRN"):
        for label, key in (("PPS", "pps"), ("KPS", "kps"), ("FAST", "fast"), ("NYHA", "nyha"), ("ECOG", "ecog")):
            value = perf.get(key)
            if not value:
                continue
            interp = get_scale_interpretation(key, value)
            meaning = interp["meaning"] if interp else None
            score_pattern = re.compile(re.escape(str(label)) + r"[^.]{0,40}" + re.escape(str(value)), re.IGNORECASE)
            score_present = bool(score_pattern.search(full_text))
            meaning_present = True
            if meaning:
                meaning_word_set = _meaning_words(meaning)
                overlap = meaning_word_set & _meaning_words(full_text)
                meaning_present = len(overlap) >= max(1, int(len(meaning_word_set) * 0.4))
            if not score_present:
                sentence = f"{label} is documented at {value}"
                sentence += f", indicating {meaning}." if meaning else "."
                missing_scale_sentences.append(sentence)
            elif meaning and not meaning_present:
                missing_scale_sentences.append(f"This {label} score reflects {meaning}.")
    if missing_scale_sentences:
        full_text = f"{full_text} " + " ".join(missing_scale_sentences)

    # scale_clinical_evidence (value/meaning/narrative/significance per
    # scale) was already computed above -- see comment there. This is what
    # makes PPS/KPS/FAST/NYHA/ECOG function as clinical evidence rather
    # than inert UI labels: Documentation Insights, LCD support, and
    # audit-support surfaces read this list directly.

    # Eligibility support is now diffused throughout the narrative (per the
    # "eligibility support should become invisible" requirement) rather than
    # isolated into its own paragraph, so there is no longer a separable
    # LCD-support block to extract. Kept as an explicit None (not removed
    # from the response) so the frontend's "Insert LCD Support Only"
    # affordance -- which already no-ops when this is falsy -- degrades
    # gracefully instead of erroring.
    lcd_support_section = None

    return {
        "ai_configured": True,
        "section1": section1,
        "section9": section9,
        "section10": section10,
        "middle_sections": full_text,
        "full_text": full_text,
        "documentation_gaps_detected": documentation_gaps_detected,
        "documentation_conflicts_detected": documentation_conflicts_detected,
        "lcd_support_section": lcd_support_section,
        "scale_clinical_evidence": scale_clinical_evidence,
    }


