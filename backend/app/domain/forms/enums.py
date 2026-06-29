from __future__ import annotations

from enum import Enum


class FormType(str, Enum):
    ASSESS = "ASSESS"
    SHORT_FORM = "SHORT_FORM"
    SUPERVISORY = "SUPERVISORY"

    ON_CALL = "ON_CALL"
    AFTER_HOURS = "AFTER_HOURS"

    MISSED_VISIT = "MISSED_VISIT"
    DECLINED_VISIT = "DECLINED_VISIT"

    DEATH_VISIT = "DEATH_VISIT"
    AFTER_DEATH = "AFTER_DEATH"

    PRE_ADMIT = "PRE_ADMIT"

    SUPPORT = "SUPPORT"


class FormFamily(str, Enum):
    CLINICAL = "CLINICAL"
    PSYCHOSOCIAL = "PSYCHOSOCIAL"
    SPIRITUAL = "SPIRITUAL"
    AIDE = "AIDE"
    ADMIN = "ADMIN"


class Discipline(str, Enum):
    RN = "RN"
    LVN = "LVN"
    NP = "NP"
    MD = "MD"

    SOCIAL_WORK = "SOCIAL_WORK"

    CHAPLAIN = "CHAPLAIN"

    HHA = "HHA"

    VOLUNTEER = "VOLUNTEER"
