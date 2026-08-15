from __future__ import annotations

from typing import Any, Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.guardrail_policy import GuardrailPolicy


class TenantSettingsService:
    """
    Tenant-scoped settings resolver.

    This service is intentionally thin. It reads from guardrail_policies
    and normalizes values for workflow services.

    Do not add workflow-specific business logic here.
    Keep this as a generic tenant settings reader.
    """

    DEFAULT_GUARDRAIL_MODE = "GUIDANCE"

    DEFAULT_IDG_REQUIRED_NOTE_DISCIPLINES = {
        "RN",
        "MSW",
        "SC",
    }

    VALID_GUARDRAIL_MODES = {
        "OFF",
        "SILENT",
        "GUIDANCE",
        "STRICT",
    }

    @staticmethod
    def _normalize_tenant_id(tenant_id: str | UUID) -> UUID:
        return tenant_id if isinstance(tenant_id, UUID) else UUID(str(tenant_id))

    @staticmethod
    def _normalize_key(policy_key: str) -> str:
        return str(policy_key or "").strip().upper()

    @staticmethod
    def _get_policy_value(
        db: Session,
        *,
        tenant_id: str | UUID,
        policy_key: str,
        default: Any = None,
    ) -> Any:
        normalized_tenant_id = TenantSettingsService._normalize_tenant_id(
            tenant_id
        )
        normalized_key = TenantSettingsService._normalize_key(policy_key)

        if not normalized_key:
            return default

        row = (
            db.query(GuardrailPolicy.value)
            .filter(
                GuardrailPolicy.tenant_id == normalized_tenant_id,
                GuardrailPolicy.policy_key == normalized_key,
                GuardrailPolicy.enabled.is_(True),
            )
            .first()
        )

        if not row:
            return default

        value = row[0]
        return default if value is None else value

    @staticmethod
    def get_guardrail_mode(
        db: Session,
        tenant_id: str | UUID,
    ) -> str:
        value = TenantSettingsService._get_policy_value(
            db,
            tenant_id=tenant_id,
            policy_key="GUARDRAIL_MODE",
            default=TenantSettingsService.DEFAULT_GUARDRAIL_MODE,
        )

        normalized = str(value or "").strip().upper()

        if normalized in TenantSettingsService.VALID_GUARDRAIL_MODES:
            return normalized

        return TenantSettingsService.DEFAULT_GUARDRAIL_MODE

    @staticmethod
    def get_policy_value(
        db: Session,
        *,
        tenant_id: str | UUID,
        policy_key: str,
        default: Any = None,
    ) -> Any:
        return TenantSettingsService._get_policy_value(
            db=db,
            tenant_id=tenant_id,
            policy_key=policy_key,
            default=default,
        )

    @staticmethod
    def get_bool_policy(
        db: Session,
        *,
        tenant_id: str | UUID,
        policy_key: str,
        default: bool,
    ) -> bool:
        value = TenantSettingsService._get_policy_value(
            db=db,
            tenant_id=tenant_id,
            policy_key=policy_key,
            default=default,
        )

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in {"TRUE", "YES", "Y", "1", "ON"}:
                return True
            if normalized in {"FALSE", "NO", "N", "0", "OFF"}:
                return False

        return bool(default)

    @staticmethod
    def get_int_policy(
        db: Session,
        *,
        tenant_id: str | UUID,
        policy_key: str,
        default: int,
    ) -> int:
        value = TenantSettingsService._get_policy_value(
            db=db,
            tenant_id=tenant_id,
            policy_key=policy_key,
            default=default,
        )

        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _normalize_discipline_set(value: Any) -> set[str]:
        if value is None:
            return set()

        raw_values: Iterable[Any]

        if isinstance(value, dict):
            raw_values = (
                value.get("disciplines")
                or value.get("required_disciplines")
                or value.get("value")
                or []
            )
        elif isinstance(value, str):
            raw_values = value.split(",")
        elif isinstance(value, (list, tuple, set)):
            raw_values = value
        else:
            raw_values = []

        disciplines = {
            str(item).strip().upper()
            for item in raw_values
            if str(item).strip()
        }

        return disciplines

    @staticmethod
    def get_idg_required_note_disciplines(
        db: Session,
        *,
        tenant_id: str | UUID,
        review_type: str | None = None,
    ) -> set[str]:
        """
        Resolve required IDG note disciplines for a tenant.

        Review-type specific policy is checked first.

        Lookup order:
            1. IDG_REQUIRED_NOTE_DISCIPLINES_<REVIEW_TYPE>
            2. IDG_REQUIRED_NOTE_DISCIPLINES
            3. DEFAULT_IDG_REQUIRED_NOTE_DISCIPLINES
        """

        if review_type:
            review_key = (
                "IDG_REQUIRED_NOTE_DISCIPLINES_"
                f"{str(review_type).strip().upper()}"
            )

            review_specific_value = TenantSettingsService._get_policy_value(
                db=db,
                tenant_id=tenant_id,
                policy_key=review_key,
                default=None,
            )

            review_specific_disciplines = (
                TenantSettingsService._normalize_discipline_set(
                    review_specific_value
                )
            )

            if review_specific_disciplines:
                return review_specific_disciplines

        tenant_value = TenantSettingsService._get_policy_value(
            db=db,
            tenant_id=tenant_id,
            policy_key="IDG_REQUIRED_NOTE_DISCIPLINES",
            default=None,
        )

        tenant_disciplines = TenantSettingsService._normalize_discipline_set(
            tenant_value
        )

        if tenant_disciplines:
            return tenant_disciplines

        return set(TenantSettingsService.DEFAULT_IDG_REQUIRED_NOTE_DISCIPLINES)