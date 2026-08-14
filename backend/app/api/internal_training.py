from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/internal/training", tags=["internal-training"])

# Training reset endpoints were removed from the field-test runtime. Production
# data changes must be controlled by explicit migration and admin workflows.