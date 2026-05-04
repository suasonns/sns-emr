import pytest
from fastapi import HTTPException

from app.core.authorization import authorize_documentation


def test_chha_can_document_chha():
    authorize_documentation(user_role="CHHA", visit_type="CHHA")


def test_chha_cannot_document_rn():
    with pytest.raises(HTTPException):
        authorize_documentation(user_role="CHHA", visit_type="RN")


def test_rn_can_document_any_discipline():
    for vt in ["RN", "CHHA", "SW", "VOLUNTEER"]:
        authorize_documentation(user_role="RN", visit_type=vt)


def test_volunteer_only_volunteer():
    authorize_documentation(user_role="VOLUNTEER", visit_type="VOLUNTEER")

    with pytest.raises(HTTPException):
        authorize_documentation(user_role="VOLUNTEER", visit_type="CHHA")


def test_alias_normalization_enforced():
    # AIDE normalizes to CHHA
    authorize_documentation(user_role="CHHA", visit_type="AIDE")

    with pytest.raises(HTTPException):
        authorize_documentation(user_role="VOLUNTEER", visit_type="AIDE")