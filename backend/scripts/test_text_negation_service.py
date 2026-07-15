from app.services.text_negation_service import (
    keyword_present,
)


def main():
    print("=" * 80)
    print("SNS TEXT NEGATION TEST")
    print("=" * 80)

    tests = [
        (
            "Weight loss noted.",
            "weight loss",
            True,
        ),
        (
            "No weight loss.",
            "weight loss",
            False,
        ),
        (
            "Denies dysphagia.",
            "dysphagia",
            False,
        ),
        (
            "Dysphagia worsening.",
            "dysphagia",
            True,
        ),
        (
            "Negative for caregiver stress.",
            "caregiver stress",
            False,
        ),
        (
            "Caregiver stress increasing.",
            "caregiver stress",
            True,
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