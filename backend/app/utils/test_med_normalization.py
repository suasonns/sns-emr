def test_normalize_text():
    assert normalize_text(" Tylenol  650 MG ") == "tylenol 650 mg"

def test_normalize_dose():
    assert normalize_dose("Morphine 5 mg") == ("5", "mg")