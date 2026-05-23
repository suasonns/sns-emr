from app.services.eligibility.lcd_loader import load_ca_hospice_lcds
from app.config.lcd.loader import load_lcd_configs

from app.rules.base import RuleContext, Workflow, DiagnosisItem
from app.rules.registry import get_rules_for_workflow
from app.rules.enforcement import apply_rules


def _select_lcd_config(patient, configs: dict):
    """
    Select disease-specific config when identifiable; otherwise fallback
    to GENERAL_DECLINE_TERMINAL_STATUS.

    Best practice:
    terminal_diagnosis_category should be explicitly set by clinician UI.
    """
    category = (
        getattr(patient, "terminal_diagnosis_category", None)
        or getattr(patient, "disease", None)
    )

    if category:
        key = str(category).strip().upper()
        if key in configs:
            return configs[key]

    return configs["GENERAL_DECLINE_TERMINAL_STATUS"]


def evaluate_hospice_eligibility(patient, admission_date):
    """
    Central hospice eligibility evaluation.

    Responsibilities:
    - Load governing LCD
    - Select disease-specific guideline
    - Run eligibility rules (evaluate-only or enforce)
    - Return eligibility context
    """

    # ---------------------------------------------------------
    # 1) Build Rule Context (NO enforcement here)
    # ---------------------------------------------------------
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
        facts={},  # EF/BNP/NYHA will be added later
    )

    # ---------------------------------------------------------
    # 2) Run eligibility rules (evaluation-only or enforce)
    # ---------------------------------------------------------
    rules = get_rules_for_workflow(ctx.workflow)
    results = [rule.evaluate(ctx) for rule in rules]

    # 🔒 Central enforcement gate
    apply_rules(results)

    # ---------------------------------------------------------
    # 3) Load CA governing LCD (L33393)
    # ---------------------------------------------------------
    lcd_index = load_ca_hospice_lcds()
    lcd = lcd_index["lcds"][0]  # CA has one governing LCD

    # ---------------------------------------------------------
    # 4) Load disease-specific + general decline configs
    # ---------------------------------------------------------
    configs = load_lcd_configs()

    guideline = _select_lcd_config(patient, configs)

    # ---------------------------------------------------------
    # 5) Evaluate disease criteria (your existing evaluator)
    # ---------------------------------------------------------
    # result = evaluate_criteria(guideline, patient, admission_date)
    # return result

    # Temporary success path (unchanged behavior)
    return {
        "eligible": True,
        "selected_guideline": guideline["disease"],
        "lcd_id": lcd.get("lcd_id"),
        "lcd_title": lcd.get("title"),
    }