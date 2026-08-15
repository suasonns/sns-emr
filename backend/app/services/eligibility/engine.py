from app.services.eligibility.lcd_loader import load_ca_hospice_lcds
from app.config.lcd.loader import load_lcd_configs

from app.services.eligibility.evidence_harvester import (
    harvest_clinical_facts,
)

from app.rules.base import RuleContext, Workflow, DiagnosisItem
from app.rules.registry import get_rules_for_workflow
from app.rules.enforcement import apply_rules


_DISEASE_ALIASES = {
    "HEART_FAILURE": {
        "heart failure", "chf", "congestive heart failure", "cad", "cardiac failure", "ischemic heart disease"
    },
    "PULMONARY_COPD_RESPIRATORY_FAILURE": {
        "copd", "respiratory failure", "hypoxia", "hypercapnia", "chronic bronchitis", "emphysema"
    },
    "ESRD_KIDNEY_DISEASE": {
        "esrd", "renal failure", "dialysis", "kidney failure", "ckd stage 5", "end stage renal disease"
    },
    "HIV_END_STAGE": {
        "hiv", "aids", "cd4", "opportunistic infection", "hiv disease"
    },
    "ALS_END_STAGE": {
        "als", "motor neuron", "amyotrophic lateral sclerosis", "bulbar", "dysphagia"
    },
    "CANCER_METASTATIC": {
        "cancer", "metastatic", "malignancy", "stage iv", "tumor", "mets", "carcinoma"
    },
    "DEMENTIA_ALZHEIMERS_SENILE_DEGENERATION": {
        "dementia", "alzheimer", "senile degeneration", "alzheimers", "neurodegenerative disease"
    },
    "LIVER_DISEASE_END_STAGE": {
        "liver disease", "cirrhosis", "liver failure", "hepatic failure", "end stage liver disease"
    },
    "STROKE_COMA": {
        "stroke", "cva", "coma", "cerebrovascular accident", "brain injury"
    },
    "GENERAL_DECLINE_TERMINAL_STATUS": {
        "general decline", "terminal status", "decline", "weight loss", "functional decline", "terminal disease"
    },
}


def _get_patient_value(patient, *keys):
    if isinstance(patient, dict):
        for key in keys:
            if key in patient:
                return patient[key]
        return None

    for key in keys:
        value = getattr(patient, key, None)
        if value is not None:
            return value
    return None


def _normalize_text(value):
    if value is None:
        return ""
    return " ".join(str(value).lower().replace("_", " ").split())


def _flatten_patient_text(patient):
    text_parts = []
    for key in [
        "primary_diagnosis_description",
        "terminal_diagnosis_category",
        "primary_diagnosis_code",
        "diagnosis",
        "disease",
        "condition",
    ]:
        value = _get_patient_value(patient, key)
        if value:
            text_parts.append(str(value))

    secondary_dx = _get_patient_value(patient, "secondary_diagnoses") or []
    if isinstance(secondary_dx, list):
        for dx in secondary_dx:
            if isinstance(dx, dict):
                text_parts.extend(filter(None, [dx.get("description"), dx.get("icd10"), dx.get("diagnosis")]))
            else:
                text_parts.append(str(dx))

    return " ".join(text_parts)


def _select_lcd_config(patient, configs: dict):
    """Select the most relevant disease-specific LCD config based on patient diagnosis and clinical context."""
    category = _get_patient_value(patient, "terminal_diagnosis_category", "disease", "primary_diagnosis_description", "diagnosis")
    if category:
        key = str(category).strip().upper().replace("-", "_")
        if key in configs:
            return configs[key]

    text = _flatten_patient_text(patient)
    text_norm = _normalize_text(text)
    for disease_key, aliases in _DISEASE_ALIASES.items():
        if any(alias in text_norm for alias in aliases):
            if disease_key in configs:
                return configs[disease_key]

    return configs["GENERAL_DECLINE_TERMINAL_STATUS"]


def _get_field_value(payload, field_name):
    if not field_name:
        return None
    current = payload
    for part in str(field_name).split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _compare(actual, expected, operator):
    op = (operator or "EQUALS").upper()
    if op == "EQUALS":
        return actual == expected
    if op == "NE":
        return actual != expected
    if op == "GT":
        return actual is not None and expected is not None and actual > expected
    if op == "GTE":
        return actual is not None and expected is not None and actual >= expected
    if op == "LT":
        return actual is not None and expected is not None and actual < expected
    if op == "LTE":
        return actual is not None and expected is not None and actual <= expected
    if op == "IN":
        if expected is None:
            return False
        return actual in expected
    return actual == expected


def _evaluate_group(group, facts):
    criteria = group.get("criteria", [])
    if not criteria:
        return True, []

    evaluated = []
    for criterion in criteria:
        actual = _get_field_value(facts, criterion.get("field"))
        expected = criterion.get("expected")
        matched = _compare(actual, expected, criterion.get("operator"))
        evaluated.append({
            "criterion_id": criterion.get("criterion_id"),
            "description": criterion.get("description"),
            "actual": actual,
            "expected": expected,
            "matched": matched,
        })

    rule = (group.get("rule") or "ALL_REQUIRED").upper()
    if rule == "ALL_REQUIRED":
        group_ok = all(item["matched"] for item in evaluated)
    elif rule == "ANY_REQUIRED":
        group_ok = any(item["matched"] for item in evaluated)
    elif rule == "ANY_3_REQUIRED":
        group_ok = sum(1 for item in evaluated if item["matched"]) >= 3
    else:
        group_ok = all(item["matched"] for item in evaluated)

    return group_ok, evaluated


def evaluate_lcd_criteria(guideline, patient=None, facts=None):
    """Evaluate a disease-specific LCD config against patient facts."""
    payload = facts or {}
    if patient is not None and not payload:
        patient_payload = {
            "scores": {
                "kps": _get_patient_value(patient, "kps"),
                "pps": _get_patient_value(patient, "pps"),
            },
            "nutrition": {
                "weight_loss_percent_6_months": _get_patient_value(patient, "weight_loss_percent_6_months"),
            },
            "functional": {
                "kps_or_pps_declining": _get_patient_value(patient, "kps_or_pps_declining"),
            },
            "adl": {
                "dependent_count": _get_patient_value(patient, "dependent_count"),
            },
        }
        payload = patient_payload

    groups = guideline.get("criteria_groups", [])
    group_results = []
    for group in groups:
        ok, details = _evaluate_group(group, payload)
        group_results.append({
            "group_id": group.get("group_id"),
            "group_name": group.get("group_name"),
            "rule": group.get("rule"),
            "passed": ok,
            "criteria": details,
        })

    overall = any(item["passed"] for item in group_results) if groups else True
    if guideline.get("group_combination_rule") == "ANY_GROUP_REQUIRED":
        overall = any(item["passed"] for item in group_results) if group_results else True

    return {
        "guideline": guideline.get("disease"),
        "eligible": overall,
        "group_results": group_results,
        "source_document": guideline.get("source_document"),
        "lcd_reference": guideline.get("lcd_reference"),
    }


def evaluate_hospice_eligibility(patient, admission_date):
    """
    Central hospice eligibility evaluation.

    Responsibilities:
    - Load governing LCD
    - Select disease-specific guideline
    - Run eligibility rules (evaluate-only or enforce)
    - Return eligibility context
    """

    ctx = RuleContext(
        tenant_id=getattr(patient, "tenant_id", None),
        patient_id=getattr(patient, "id", None),
        workflow=Workflow.ADMISSION,
        admission_date=admission_date,
        primary_dx=DiagnosisItem(
            icd10=getattr(patient, "primary_diagnosis_code", None),
            description=getattr(patient, "primary_diagnosis_description", None),
        ),
        secondary_dx=[
            DiagnosisItem(
                icd10=dx.icd10,
                description=getattr(dx, "description", None),
                is_related_to_primary=getattr(dx, "is_related", None),
            )
            for dx in getattr(patient, "secondary_diagnoses", [])
        ],
        facts=harvest_clinical_facts(patient),
    )

    rules = get_rules_for_workflow(ctx.workflow)
    results = [rule.evaluate(ctx) for rule in rules]
    apply_rules(results)

    lcd_index = load_ca_hospice_lcds()
    lcd = lcd_index["lcds"][0]

    configs = load_lcd_configs()
    guideline = _select_lcd_config(patient, configs)

    facts = {
        "scores": {
            "kps": _get_patient_value(patient, "kps"),
            "pps": _get_patient_value(patient, "pps"),
        },
        "nutrition": {
            "weight_loss_percent_6_months": _get_patient_value(patient, "weight_loss_percent_6_months"),
        },
        "functional": {
            "kps_or_pps_declining": _get_patient_value(patient, "kps_or_pps_declining"),
        },
        "adl": {
            "dependent_count": _get_patient_value(patient, "dependent_count"),
        },
    }
    criteria_result = evaluate_lcd_criteria(guideline, patient=patient, facts=facts)

    return {
        "eligible": criteria_result["eligible"],
        "selected_guideline": guideline["disease"],
        "lcd_id": lcd.get("lcd_id"),
        "lcd_title": lcd.get("title"),
        "source_document": guideline.get("source_document"),
        "lcd_reference": guideline.get("lcd_reference"),
        "criteria_summary": criteria_result,
    }