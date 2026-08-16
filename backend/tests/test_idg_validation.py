from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.idg_note import IDGNote
from app.models.idg_review import IDGReview
from app.services.idg_completeness import (
    validate_idg_completeness,
)


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def review(
    db_session,
    tenant_id,
):
    review = IDGReview(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=uuid.uuid4(),
        idg_meeting_id=uuid.uuid4(),
        benefit_period_id=uuid.uuid4(),
        review_date=datetime.now(timezone.utc),
        summary="Test IDG Review",
        poc_action="No changes",
        is_finalized=False,

        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_session.add(review)
    db_session.commit()

    return review


def create_note(
    db_session,
    review,
    tenant_id,
    discipline,
    note="valid note",
):
    note_record = IDGNote(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=review.patient_id,
        idg_review_id=review.id,
        discipline=discipline,
        note=note,
    )

    db_session.add(note_record)
    db_session.commit()

    return note_record


# =========================================================
# IDG COMPLETENESS TESTS
# =========================================================


def test_idg_incomplete_missing_disciplines(
    db_session,
    review,
    tenant_id,
):
    create_note(
        db_session,
        review,
        tenant_id,
        "RN",
    )

    missing = validate_idg_completeness(
        db_session,
        idg_review_id=review.id,
        tenant_id=tenant_id,
    )

    assert "MSW_note_missing" in missing
    assert "MD_note_missing" in missing
    assert "SC_note_missing" in missing


def test_idg_complete_success(
    db_session,
    review,
    tenant_id,
):
    create_note(
        db_session,
        review,
        tenant_id,
        "RN",
    )

    create_note(
        db_session,
        review,
        tenant_id,
        "MSW",
    )

    create_note(
        db_session,
        review,
        tenant_id,
        "MD",
    )

    create_note(
        db_session,
        review,
        tenant_id,
        "SC",
    )

    missing = validate_idg_completeness(
        db_session,
        idg_review_id=review.id,
        tenant_id=tenant_id,
    )

    assert missing == []


def test_empty_note_fails(
    db_session,
    review,
    tenant_id,
):
    create_note(
        db_session,
        review,
        tenant_id,
        "RN",
    )

    create_note(
        db_session,
        review,
        tenant_id,
        "MSW",
    )

    create_note(
        db_session,
        review,
        tenant_id,
        "MD",
    )

    create_note(
        db_session,
        review,
        tenant_id,
        "SC",
        note="",
    )

    missing = validate_idg_completeness(
        db_session,
        idg_review_id=review.id,
        tenant_id=tenant_id,
    )

    assert "SC_note_empty" in missing


def test_duplicate_discipline_blocked_by_database(
    db_session,
    review,
    tenant_id,
):
    create_note(
        db_session,
        review,
        tenant_id,
        "RN",
    )

    with pytest.raises(IntegrityError):
        create_note(
            db_session,
            review,
            tenant_id,
            "RN",
        )

    db_session.rollback()


def test_wrong_tenant_isolated(
    db_session,
    review,
    tenant_id,
):
    create_note(
        db_session,
        review,
        tenant_id,
        "RN",
    )

    missing = validate_idg_completeness(
        db_session,
        idg_review_id=review.id,
        tenant_id=uuid.uuid4(),
    )

    assert "IDG_REVIEW_NOT_FOUND" in missing