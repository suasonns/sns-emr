from app.core.audit_middleware import audit_middleware
from fastapi import FastAPI, Depends
from app.api import auth
from app.core.permissions import require_roles
from app.core.auth import CurrentUser

app = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
)

app.middleware("http")(audit_middleware)

# Register auth router
app.include_router(auth.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/patients")
def list_patients(
    user: CurrentUser = Depends(
        require_roles(["RN", "NP", "MD", "Surveyor"])
    )
):
    return {
        "message": "Access granted",
        "user_id": user.user_id,
        "role": user.role,
    }