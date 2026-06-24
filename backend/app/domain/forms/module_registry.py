from __future__ import annotations

# Reusable module keys.  These are not UI forms by themselves;
# they are attachable building blocks the form engine can combine.

MODULE_REGISTRY = {
    "pain": {
        "description": "Pain assessment / pain impact / observed pain depending on discipline"
    },
    "vitals": {
        "description": "Vital signs"
    },
    "symptoms": {
        "description": "Symptom review / symptom tracking"
    },
    "narrative": {
        "description": "Narrative free-text / structured narrative"
    },
    "skin": {
        "description": "Structured skin assessment (RN/NP only for full structured ownership)"
    },
    "fall_risk": {
        "description": "Structured fall risk assessment (RN/NP only for full structured ownership)"
    },
    "safety": {
        "description": "Structured safety assessment (RN/NP only for full structured ownership)"
    },
    "functional_scores": {
        "description": "KPS / PPS / FAST / related functional scoring"
    },
    "orders_support": {
        "description": "Order capture / order support / escalation support"
    },
    "supervisory": {
        "description": "Supervisory visit module"
    },
    "death": {
        "description": "Death visit / after-death workflow support"
    },
    "bereavement": {
        "description": "Bereavement assessment and follow-up support"
    },
    "complaint": {
        "description": "Caller complaint / presenting concern"
    },
    "action_taken": {
        "description": "Triage action / escalation action / follow-up action"
    },
    "care_provided": {
        "description": "Care provided / aide support / supportive services"
    },
    "spiritual_distress": {
        "description": "Spiritual distress / spiritual suffering / support requested"
    },
    "psychosocial": {
        "description": "Psychosocial assessment / family coping / social support"
    },
}