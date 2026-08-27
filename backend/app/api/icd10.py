from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.services.icd10_resolver_service import search_icd10_diagnoses

router = APIRouter(prefix="/icd10", tags=["icd10"])


@router.get("/search", summary="Search the ICD-10 master list for diagnosis typeahead suggestions")
def icd10_search(
    query: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC", "Surveyor"])
    ),
):
    """
    Backs the Primary/Secondary Diagnosis typeahead on the Facesheet (and any
    other diagnosis-entry field) so staff can search by ICD-10 code or free
    text description and pick an official coded diagnosis instead of typing
    an unvalidated string.
    """
    query = (query or "").strip()
    if len(query) < 2:
        return {"query": query, "suggestions": []}

    suggestions = search_icd10_diagnoses(db, query_text=query, limit=25)
    return {"query": query, "suggestions": suggestions}
