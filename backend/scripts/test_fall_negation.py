from app.services.text_negation_service import (
    keyword_present,
)


def main():
    print("=" * 80)
    print("SNS FALL NEGATION TEST")
    print("=" * 80)

    tests = [
        (
            "Patient experienced multiple falls.",
            "falls",
            True,
        ),
        (
            "Patient is a fall risk.",
            "fall risk",
            True,
        ),
        (
            "No falls reported.",
            "falls",
            False,
        ),
        (
            "Denies falls.",
            "falls",
            False,
        ),
        (
            "No fall risk identified.",
            "fall risk",
            False,
        ),
        (
            "Home environment is unsafe.",
            "unsafe",
            True,
        ),
        (
            "Home environment is not unsafe.",
            "unsafe",
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