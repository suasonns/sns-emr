from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.core.flag_rules_loader import load_flag_rules


@dataclass(frozen=True)
class FlagResult:
    is_flagged: bool
    tier: Optional[str]
    matched_rule_ids: List[str]


def _text_contains_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def _is_negated(text: str, phrase: str, negations: List[str], window: int) -> bool:
    """
    If any negation phrase appears within `window` chars before phrase, treat as negated.
    """
    t = text.lower()
    p = phrase.lower()
    idx = t.find(p)
    if idx < 0:
        return False
    start = max(0, idx - window)
    prefix = t[start:idx]
    return any(n.lower() in prefix for n in negations)


def evaluate_document_flags(
    *,
    document_type: str,
    extracted_values: Dict[str, Any],
    document_text: str,
) -> FlagResult:
    ruleset = load_flag_rules()
    rules = ruleset.get("rules", [])
    neg_window = ruleset.get("evaluation_logic", {}).get("negation_window_chars", 40)

    matched: List[Tuple[str, str]] = []  # (rule_id, tier)

    # Only evaluate for target document types (still notify regardless elsewhere)
    applies = set(ruleset.get("applies_to_document_types", []))
    if applies and document_type not in applies:
        return FlagResult(is_flagged=False, tier=None, matched_rule_ids=[])

    for r in rules:
        rid = r.get("id")
        tier = r.get("tier", "TIER_2")
        match_type = r.get("match_type")

        if match_type == "structured_value":
            field = r.get("field")
            op = r.get("operator")
            val = r.get("value")

            if field not in extracted_values:
                continue

            try:
                actual = float(extracted_values[field])
                target = float(val)
            except Exception:
                continue

            ok = False
            if op == "<":
                ok = actual < target
            elif op == "<=":
                ok = actual <= target
            elif op == ">":
                ok = actual > target
            elif op == ">=":
                ok = actual >= target

            if ok:
                matched.append((rid, tier))

        elif match_type == "text_phrase":
            phrases_any = r.get("phrases_any", []) or []
            neg_any = r.get("phrases_negated_any", []) or []

            # Match any phrase unless negated
            for phrase in phrases_any:
                if _text_contains_phrase(document_text, phrase):
                    if _is_negated(document_text, phrase, neg_any, neg_window):
                        continue
                    matched.append((rid, tier))
                    break

    if not matched:
        return FlagResult(is_flagged=False, tier=None, matched_rule_ids=[])

    # Tier priority: if any Tier 1 matched, Tier 1 wins
    tiers = [t for _, t in matched]
    final_tier = "TIER_1" if "TIER_1" in tiers else "TIER_2"

    return FlagResult(
        is_flagged=True,
        tier=final_tier,
        matched_rule_ids=[rid for rid, _ in matched],
    )