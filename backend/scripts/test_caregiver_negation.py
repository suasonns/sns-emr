from app.services.text_negation_service import (
    keyword_present,
)


def main():
    tests = [
        (
            "Caregiver stress increasing.",
            "caregiver stress",
            True,
        ),
        (
            "No caregiver stress.",
            "caregiver stress",
            False,
        ),
        (
            "Negative for caregiver stress.",
            "caregiver stress",
            False,
        ),
        (
            "Caregiver requires additional support.",
            "caregiver",
            True,
        ),
        (
            "No caregiver concerns identified.",
            "caregiver",
            False,
        ),
    ]

    for text, keyword, expected in tests:
        actual = keyword_present(
            text,
            keyword,
        )

        status = (
            "PASS"
            if actual == expected
            else "FAIL"
        )

        print(
            f"{status} | "
            f"Text='{text}' | "
            f"Keyword='{keyword}' | "
            f"Expected={expected} | "
            f"Actual={actual}"
        )


if __name__ == "__main__":
    main()