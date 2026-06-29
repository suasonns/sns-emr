from app.utils.med_normalization import normalize_text, normalize_dose
from app.utils.drug_alias import normalize_drug_name


def test_normalize_text():
    assert normalize_text(" Tylenol  650 MG ") == "tylenol 650 mg"


def test_normalize_drug_name():
    assert normalize_drug_name(" Tylenol ") == "tylenol"
    assert normalize_drug_name("Morphine Sulfate") == "morphine sulfate"
    assert normalize_drug_name(None) == ""


def test_normalize_dose_mass_units():
    assert normalize_dose("1 g") == "1000mg"
    assert normalize_dose("1000 mcg") == "1mg"
    assert normalize_dose("1.5 G") == "1500mg"
    assert normalize_dose("500 ug") == "0.5mg"


def test_normalize_dose_preserves_complex_formats():
    assert normalize_dose("10 mg/ml") == "10 mg/ml"
    assert normalize_dose("1 patch daily") == "1 patch daily"
    assert normalize_dose("2 tabs BID") == "2 tabs bid"


def test_normalize_dose_empty_inputs():
    assert normalize_dose("") == ""
    assert normalize_dose(None) == ""
