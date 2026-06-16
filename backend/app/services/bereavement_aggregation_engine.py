from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID


# =========================================================
# INPUT MODEL
# =========================================================

@dataclass(frozen=True)
class BereavementNoteInput:
    patient_id: UUID
    note_id: Optional[UUID]
    discipline: str
    text: Optional[str]


# =========================================================
# OUTPUT MODEL
# =========================================================

@dataclass
class BereavementAggregationResult:
    rn_present: bool = False
    sw_present: bool = False
    chaplain_present: bool = False

    source_notes: List[UUID] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)


# =========================================================
# ENGINE
# =========================================================

class BereavementAggregationEngine:
    """
    Interdisciplinary bereavement aggregation engine.

    DESIGN:
    - Conservative keyword detection
    - Discipline-specific evidence
    - Non-blocking usage
    """

    BEREAVEMENT_KEYWORDS = [
        "grief",
        "bereavement",
        "mourning",
        "loss",
        "death",
        "anticipatory grief",
    ]

    def detect(
        self,
        notes: List[BereavementNoteInput],
    ) -> BereavementAggregationResult:

        result = BereavementAggregationResult()

        for note in notes:
            discipline = (note.discipline or "").upper()
            text = (note.text or "").lower()

            if not text:
                continue

            # ✅ keyword match (conservative)
            if not any(k in text for k in self.BEREAVEMENT_KEYWORDS):
                continue

            # ✅ discipline mapping
            if discipline == "RN":
                result.rn_present = True
                result.reason_codes.append("RN_BEREAVEMENT_TEXT")

            elif discipline in ["SW", "MSW", "LCSW"]:
                result.sw_present = True
                result.reason_codes.append("SW_BEREAVEMENT_TEXT")

            elif discipline == "CHAPLAIN":
                result.chaplain_present = True
                result.reason_codes.append("CHAPLAIN_BEREAVEMENT_TEXT")

            if note.note_id:
                result.source_notes.append(note.note_id)

        return result