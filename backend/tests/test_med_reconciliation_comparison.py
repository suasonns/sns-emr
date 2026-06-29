from app.services.med_reconciliation_comparison import (
    compare_imported_medication_to_existing,
    compare_imported_item_against_med_list,
)


def test_exact_normalized_match():
    imported_item = {
        "med_name_raw": " Morphine Sulfate ",
        "med_name_normalized": "morphine sulfate",
        "dose": "1.5 G",
        "dose_normalized": "1500mg",
        "route_normalized": "po",
        "frequency_normalized": "q4h prn",
    }

    existing_medication = {
        "id": "123",
        "medication_name": "Morphine Sulfate",
        "canonical_name": "morphine sulfate",
        "dose": "1500 mg",
        "dose_normalized": "1500mg",
        "route_normalized": "po",
        "frequency_normalized": "q4h prn",
    }

    result = compare_imported_medication_to_existing(
        imported_item=imported_item,
        existing_medication=existing_medication,
    )

    assert result.match_type == "EXACT_NORMALIZED_MATCH"
    assert result.matched is True
    assert result.requires_review is False
    assert result.discrepancy_flags == []


def test_partial_match_with_dose_mismatch():
    imported_item = {
        "med_name_raw": " Morphine Sulfate ",
        "med_name_normalized": "morphine sulfate",
        "dose": "1 g",
        "dose_normalized": "1000mg",
        "route_normalized": "po",
        "frequency_normalized": "q4h prn",
    }

    existing_medication = {
        "id": "123",
        "medication_name": "Morphine Sulfate",
        "canonical_name": "morphine sulfate",
        "dose": "1500 mg",
        "dose_normalized": "1500mg",
        "route_normalized": "po",
        "frequency_normalized": "q4h prn",
    }

    result = compare_imported_medication_to_existing(
        imported_item=imported_item,
        existing_medication=existing_medication,
    )

    assert result.match_type == "PARTIAL_MATCH_WITH_DISCREPANCY"
    assert result.matched is True
    assert result.requires_review is True
    assert "DOSE_MISMATCH" in result.discrepancy_flags


def test_no_match_in_active_med_list():
    imported_item = {
        "med_name_raw": " Lorazepam ",
        "med_name_normalized": "lorazepam",
        "dose": "1 mg",
        "dose_normalized": "1mg",
        "route_normalized": "po",
        "frequency_normalized": "q4h prn",
    }

    existing_medications = [
        {
            "id": "123",
            "medication_name": "Morphine Sulfate",
            "canonical_name": "morphine sulfate",
            "dose": "1500 mg",
            "dose_normalized": "1500mg",
            "route_normalized": "po",
            "frequency_normalized": "q4h prn",
        }
    ]

    result = compare_imported_item_against_med_list(
        imported_item=imported_item,
        existing_medications=existing_medications,
    )

    assert result.match_type == "NO_MATCH_IN_ACTIVE_MED_LIST"
    assert result.matched is False
    assert result.requires_review is True
    assert "MISSING_FROM_ACTIVE_MED_LIST" in result.discrepancy_flags
