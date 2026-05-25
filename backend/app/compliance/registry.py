from __future__ import annotations

from typing import Dict, List
from app.compliance.types import Regulator

# CMS
from app.compliance.cms import poc_update as cms_poc_update
from app.compliance.cms import evidence as cms_evidence

# ACHC
from app.compliance.achc import documentation_timeliness as achc_doc

# CDPH
from app.compliance.cdph import california_specific as cdph_ca

# TJC
from app.compliance.tjc import survey_tracers as tjc_tracers

# CHAP
from app.compliance.chap import chap_core as chap_core


ACTIVE_RULEPACKS: Dict[Regulator, List[object]] = {
    "CMS": [
        cms_poc_update,
        cms_evidence,
    ],
    "ACHC": [
        achc_doc,
    ],
    "CDPH": [
        cdph_ca,
    ],
    "TJC": [
        tjc_tracers,
    ],
    "CHAP": [
        chap_core,
    ],
}