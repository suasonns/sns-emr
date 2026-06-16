from fastapi import APIRouter

from app.billing.store import get_all_tenants

router = APIRouter(prefix="/billing", tags=["Billing Tenants"])


@router.get("/tenants")
def get_tenants():
    return get_all_tenants()
