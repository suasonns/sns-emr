from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

CANONICAL_TREATMENT_DOMAINS = frozenset({"TREATMENT", "TREATMENT_LIMITATION"})

IMPORTER_AUTHORITY = {
    "expand_ontology_phase2_neurologic": 20,
    "complete_ontology_phase2_neurologic_coverage": 30,
    "complete_ontology_neurologic_clinical_reasoning": 30,
    "populate_ontology_ak_neuro_cardio": 10,
    "populate_ontology_ak_pulmonary_copd_crf": 10,
    "populate_ontology_ak_renal_ckd_esrd": 10,
    "import_neurologic_production_source_manifest": 100,
    "import_dementia_production_hardening": 100,
    "import_cardiovascular_production_source_manifest": 100,
    "import_pulmonary_production_source_manifest": 100,
    "import_renal_production_source_manifest": 100,
    "import_hiv_production_source_manifest": 100,
    "import_liver_production_source_manifest": 100,
    "import_als_production_source_manifest": 100,
    "import_oncology_foundation_v1": 100,
    "import_breast_cancer_production_identity_manifest": 100,
    "import_colorectal_rectal_cancer_production_identity_manifest": 100,
    "import_lung_cancer_production_identity_manifest": 100,
}

LIMITATION_CATEGORY_PREFERENCE = {
    frozenset({"CONTRAINDICATED", "TREATMENT_CONTRAINDICATED"}): "CONTRAINDICATED",
    frozenset({"DECLINED", "TREATMENT_DECLINED"}): "DECLINED",
    frozenset({"DISCONTINUED", "TREATMENT_DISCONTINUED"}): "DISCONTINUED",
    frozenset({"NOT_TOLERATED", "TREATMENT_INTOLERANT"}): "NOT_TOLERATED",
    frozenset({"NOT_CANDIDATE", "NOT_A_CANDIDATE"}): "NOT_CANDIDATE",
    frozenset({"GOALS_OF_CARE", "COMFORT_FOCUSED"}): "GOALS_OF_CARE",
    frozenset({"NOT_BENEFICIAL", "NOT_A_CANDIDATE"}): "NOT_BENEFICIAL",
}

TREATMENT_CATEGORY_PREFERENCE = {
    ("serial casting", frozenset({"DISEASE_DIRECTED", "SUPPORTIVE"})): "DISEASE_DIRECTED",
}


def normalize_ontology_concept_name(name: str) -> str:
    if name is None:
        raise ValueError("Ontology concept name cannot be None.")
    collapsed = re.sub(r"\s+", " ", name.strip())
    if not collapsed:
        raise ValueError("Ontology concept name cannot be empty or whitespace-only.")
    return collapsed.lower()


def normalize_category_token(category: str | None) -> str | None:
    if category is None:
        return None
    normalized = re.sub(r"\s+", "_", category.strip().upper())
    return normalized or None


def importer_authority(importer_name: str) -> int:
    return IMPORTER_AUTHORITY.get(importer_name, 0)


def concept_identity_key(domain: str, name: str) -> str:
    if domain in CANONICAL_TREATMENT_DOMAINS:
        return normalize_ontology_concept_name(name)
    return name.strip().lower()


@dataclass(frozen=True)
class CategoryReconciliation:
    action: str
    category: str
    changed: bool


class DuplicateCanonicalIdentityError(RuntimeError):
    def __init__(
        self,
        *,
        table_name: str,
        disease_id,
        normalized_name: str,
        row_ids: Sequence,
        categories: Sequence[str],
        importer_name: str,
    ) -> None:
        self.table_name = table_name
        self.disease_id = disease_id
        self.normalized_name = normalized_name
        self.row_ids = list(row_ids)
        self.categories = list(categories)
        self.importer_name = importer_name
        super().__init__(
            f"Duplicate canonical identity in {table_name}: disease_id={disease_id}, "
            f"normalized_name={normalized_name!r}, row_ids={self.row_ids}, "
            f"categories={self.categories}, importer={importer_name!r}"
        )


class CategoryConflictRequiresReview(RuntimeError):
    def __init__(
        self,
        *,
        domain: str,
        disease_id,
        normalized_name: str,
        existing_row_id,
        existing_display_name: str,
        existing_category: str,
        incoming_display_name: str,
        incoming_category: str,
        importer_name: str,
    ) -> None:
        self.domain = domain
        self.disease_id = disease_id
        self.normalized_name = normalized_name
        self.existing_row_id = existing_row_id
        self.existing_display_name = existing_display_name
        self.existing_category = existing_category
        self.incoming_display_name = incoming_display_name
        self.incoming_category = incoming_category
        self.importer_name = importer_name
        super().__init__(
            f"Category conflict requires review for {domain}: disease_id={disease_id}, "
            f"normalized_name={normalized_name!r}, existing_row_id={existing_row_id}, "
            f"existing_category={existing_category!r}, incoming_category={incoming_category!r}, "
            f"importer={importer_name!r}"
        )


def existing_rows_by_canonical_name(
    rows: Sequence,
    *,
    domain: str,
    table_name: str,
    disease_id,
    importer_name: str,
    name_attr: str,
    category_attr: str | None = None,
) -> dict[str, object]:
    indexed: dict[str, list[object]] = {}
    for row in rows:
        normalized_name = getattr(row, "normalized_name", None) or concept_identity_key(domain, getattr(row, name_attr))
        indexed.setdefault(normalized_name, []).append(row)

    collapsed: dict[str, object] = {}
    for normalized_name, group in indexed.items():
        if len(group) > 1:
            categories = [getattr(row, category_attr) for row in group] if category_attr else [""] * len(group)
            raise DuplicateCanonicalIdentityError(
                table_name=table_name,
                disease_id=disease_id,
                normalized_name=normalized_name,
                row_ids=[row.id for row in group],
                categories=categories,
                importer_name=importer_name,
            )
        collapsed[normalized_name] = group[0]
    return collapsed


def preferred_category_for_conflict(
    *,
    domain: str,
    normalized_name: str,
    existing_category: str,
    incoming_category: str,
) -> str | None:
    pair = frozenset({existing_category, incoming_category})
    if domain == "TREATMENT_LIMITATION":
        return LIMITATION_CATEGORY_PREFERENCE.get(pair)
    return TREATMENT_CATEGORY_PREFERENCE.get((normalized_name, pair))


def reconcile_category(
    *,
    domain: str,
    disease_id,
    normalized_name: str,
    existing_row_id,
    existing_display_name: str,
    existing_category: str,
    incoming_display_name: str,
    incoming_category: str,
    importer_name: str,
) -> CategoryReconciliation:
    existing_token = normalize_category_token(existing_category)
    incoming_token = normalize_category_token(incoming_category)
    if existing_token == incoming_token:
        action = "UNCHANGED" if existing_category == incoming_category else "NORMALIZED_EQUIVALENT"
        return CategoryReconciliation(action=action, category=existing_category, changed=False)

    preferred = preferred_category_for_conflict(
        domain=domain,
        normalized_name=normalized_name,
        existing_category=existing_category,
        incoming_category=incoming_category,
    )
    if preferred is not None:
        if existing_category == preferred:
            return CategoryReconciliation(action="UNCHANGED", category=existing_category, changed=False)
        if incoming_category == preferred:
            return CategoryReconciliation(
                action="UPDATED_FROM_AUTHORITATIVE_SOURCE",
                category=incoming_category,
                changed=True,
            )

    raise CategoryConflictRequiresReview(
        domain=domain,
        disease_id=disease_id,
        normalized_name=normalized_name,
        existing_row_id=existing_row_id,
        existing_display_name=existing_display_name,
        existing_category=existing_category,
        incoming_display_name=incoming_display_name,
        incoming_category=incoming_category,
        importer_name=importer_name,
    )
