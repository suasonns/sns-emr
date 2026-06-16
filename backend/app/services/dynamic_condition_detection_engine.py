from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID


# =========================================================
# OUTPUT CONTRACT (LOCKED)
# =========================================================

@dataclass(frozen=True)
class ConditionDetectionResult:
    has_wounds: bool
    psychosocial_issue: bool
    spiritual_distress: bool
    bereavement_flag: bool

    reason_codes: List[str]


# =========================================================
# INPUT MODELS
# =========================================================

@dataclass(frozen=True)
class NoteInput:
    patient_id: UUID
    author_discipline: str  # RN / MSW / LCSW / CHAPLAIN
    text: Optional[str]
    structured_flags: Optional[dict]


@dataclass(frozen=True)
class AssessmentInput:
    patient_id: UUID
    has_wounds: Optional[bool] = None
    psychosocial_issue: Optional[bool] = None
    spiritual_distress: Optional[bool] = None
    bereavement_flag: Optional[bool] = None


# =========================================================
# ENGINE
# =========================================================

class DynamicConditionDetectionEngine:

    # 🔒 Conservative detection (compliance-safe)
    WOUND_KEYWORDS = ["wound", "ulcer", "pressure injury", "lesion"]
    PSYCHOSOCIAL_KEYWORDS = ["anxiety", "depression", "family conflict", "caregiver stress"]
    SPIRITUAL_KEYWORDS = ["spiritual distress", "loss of faith", "existential", "meaninglessness"]
    BEREAVEMENT_KEYWORDS = ["grief", "anticipatory grief", "loss", "mourning"]

    def detect(
        self,
        notes: Optional[List[NoteInput]] = None,
        assessments: Optional[List[AssessmentInput]] = None,
    ) -> ConditionDetectionResult:

        has_wounds = False
        psychosocial_issue = False
        spiritual_distress = False
        bereavement_flag = False

        reasons: set[str] = set()

        # ✅ normalize inputs
        notes = notes or []
        assessments = assessments or []

        # =========================================================
        # 1. STRUCTURED DATA (HIGHEST TRUST)
        # =========================================================
        for a in assessments:

            if a.has_wounds:
                has_wounds = True
                reasons.add("STRUCTURED_WOUND_FLAG")

            if a.psychosocial_issue:
                psychosocial_issue = True
                reasons.add("STRUCTURED_PSYCHOSOCIAL_FLAG")

            if a.spiritual_distress:
                spiritual_distress = True
                reasons.add("STRUCTURED_SPIRITUAL_FLAG")

            if a.bereavement_flag:
                bereavement_flag = True
                reasons.add("STRUCTURED_BEREAVEMENT_FLAG")

        # =========================================================
        # 2. TEXT DETECTION (CONSERVATIVE)
        # =========================================================
        for note in notes:

            text = (note.text or "").lower()
            discipline = (note.author_discipline or "").upper()

            if not text:
                continue

            # WOUNDS
            if any(k in text for k in self.WOUND_KEYWORDS):
                has_wounds = True
                reasons.add(f"TEXT_WOUND_{discipline}")

            # PSYCHOSOCIAL
            if discipline in ["MSW", "LCSW", "RN"]:
                if any(k in text for k in self.PSYCHOSOCIAL_KEYWORDS):
                    psychosocial_issue = True
                    reasons.add(f"TEXT_PSYCHOSOCIAL_{discipline}")

            # SPIRITUAL
            if discipline == "CHAPLAIN":
                if any(k in text for k in self.SPIRITUAL_KEYWORDS):
                    spiritual_distress = True
                    reasons.add("TEXT_SPIRITUAL_CHAPLAIN")

            # BEREAVEMENT
            if any(k in text for k in self.BEREAVEMENT_KEYWORDS):
                bereavement_flag = True
                reasons.add(f"TEXT_BEREAVEMENT_{discipline}")

        return ConditionDetectionResult(
            has_wounds=has_wounds,
            psychosocial_issue=psychosocial_issue,
            spiritual_distress=spiritual_distress,
            bereavement_flag=bereavement_flag,
            reason_codes=sorted(list(reasons)),
        )