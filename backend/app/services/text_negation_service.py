from __future__ import annotations

import re


NEGATION_TERMS = (
    "no",
    "not",
    "without",
    "denies",
    "deny",
    "denied",
    "negative for",
    "absence of",
    "free of",
    "not experiencing",
    "not reporting",
)


def keyword_present(
    text: str | None,
    keyword: str,
) -> bool:
    """
    Determine whether a keyword is present and not negated.

    Examples:

        "weight loss noted"
            -> True

        "no weight loss"
            -> False

        "denies dysphagia"
            -> False

        "caregiver stress worsening"
            -> True

        "negative for caregiver stress"
            -> False

    This service is intentionally conservative.

    If uncertainty exists, the keyword is considered
    present only when it appears without an obvious
    negation phrase immediately preceding it.
    """

    if not text:
        return False

    normalized_text = _normalize(text)
    normalized_keyword = _normalize(keyword)

    if normalized_keyword not in normalized_text:
        return False

    if _is_negated(
        normalized_text,
        normalized_keyword,
    ):
        return False

    return True


def any_keyword_present(
    text: str | None,
    keywords: list[str],
) -> bool:
    """
    Returns True if any keyword is present and not negated.
    """

    for keyword in keywords:
        if keyword_present(text, keyword):
            return True

    return False


def _is_negated(
    text: str,
    keyword: str,
) -> bool:
    """
    Detect common hospice documentation patterns.

    Examples:

        no weight loss
        denies dysphagia
        negative for edema
        without caregiver stress

    Window is intentionally limited to reduce
    false negatives.
    """

    escaped_keyword = re.escape(keyword)

    for term in NEGATION_TERMS:
        escaped_term = re.escape(term)

        pattern = (
            r"\b"
            + escaped_term
            + r"\s+"
            + r"(?:\w+\s+){0,3}?"
            + escaped_keyword
            + r"\b"
        )

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return True

    return False


def _normalize(
    value: str,
) -> str:
    """
    Normalize text for matching.
    """

    value = value.lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()