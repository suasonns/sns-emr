from uuid import uuid4
from app.services.dynamic_condition_detection_engine import (
    DynamicConditionDetectionEngine,
    NoteInput,
)


def test_wound_detection_from_text():
    engine = DynamicConditionDetectionEngine()
    patient_id = uuid4()

    notes = [
        NoteInput(
            patient_id=patient_id,
            author_discipline="RN",
            text="Patient has pressure ulcer on sacrum",
            structured_flags=None
        )
    ]

    result = engine.detect(notes=notes)

    assert result.has_wounds is True


def test_psychosocial_detection_from_msw():
    engine = DynamicConditionDetectionEngine()
    patient_id = uuid4()

    notes = [
        NoteInput(
            patient_id=patient_id,
            author_discipline="MSW",
            text="Caregiver stress and anxiety observed",
            structured_flags=None
        )
    ]

    result = engine.detect(notes=notes)

    assert result.psychosocial_issue is True


def test_spiritual_detection_requires_chaplain():
    engine = DynamicConditionDetectionEngine()
    patient_id = uuid4()

    notes = [
        NoteInput(
            patient_id=patient_id,
            author_discipline="RN",
            text="Spiritual distress mentioned",
            structured_flags=None
        )
    ]

    result = engine.detect(notes=notes)

    assert result.spiritual_distress is False