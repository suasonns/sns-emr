from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.poc_rule_loader import (
    get_all_rules,
    get_rule_by_icd,
    get_rules_version,
)


def main():
    rules = get_all_rules()

    print("=" * 80)
    print("SNS POC RULE LOADER TEST")
    print("=" * 80)

    print(f"Version: {get_rules_version()}")
    print(f"Rule Count: {len(rules)}")

    print()

    for code in ["I50", "J44", "F03"]:
        rule = get_rule_by_icd(code)

        if not rule:
            print(f"[FAILED] {code} NOT FOUND")
            continue

        print(f"[PASS] {code}")
        print(f"Condition: {rule.get('condition')}")

        print("Problems:")
        for problem in rule.get("problems", []):
            print(f"  - {problem['code']}")

        print("Goals:")
        print(f"  - {len(rule.get('goals', []))}")

        print("Interventions:")
        print(f"  - {len(rule.get('interventions', []))}")

        print()

    print("=" * 80)
    print("RULE LOADER TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()