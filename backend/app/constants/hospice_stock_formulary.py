"""
Curated list of standard hospice "comfort kit" / stock medications with the
strength, form, and route the agency actually stocks and orders in practice
(e.g. Morphine Sulfate / Roxanol at 20 MG/ML oral concentrate, given
sublingually) — as opposed to the dozens of other RxNorm-listed strengths for
the same ingredient that are rarely, if ever, used in hospice.

These are surfaced FIRST (ahead of general RxNorm matches) in the medication
typeahead so clinicians are nudged toward the agency's real-world stock dose
instead of picking an arbitrary strength.

Each entry carries both `generic_name` and `brand_name` plus a
`recommended_dosing` string (standard/market-recommended adult dosing) so that
typing EITHER the brand or the generic name surfaces the same normalized
entry — e.g. typing "Tylenol" surfaces "Acetaminophen (Tylenol)" with its
recommended dosing, not just the raw brand name.

`relative_cost_rank` (1 = cheapest) and `pharmacy_available` support the
"same therapeutic family" alternatives box: when a clinician picks a
medication, other stock meds sharing a drug class (per
app/config/drug_classes.json) are shown cheapest-first, and if the selected
med isn't available in the pharmacy, its alternatives are recommended in the
same cost order. `pharmacy_available` is a placeholder flag (all True today,
no live inventory feed yet) an admin can flip when a specific stock item is
temporarily out of stock.

Not exhaustive — extend as new comfort-kit / commonly-ordered hospice
medications come up. This is reference data only; it does not restrict what
can be ordered (any RxNorm match or free-text/compounded entry is still
allowed).
"""

HOSPICE_STOCK_FORMULARY = [
    {
        "generic_name": "Morphine Sulfate",
        "brand_name": "Roxanol",
        "name": "Morphine Sulfate Oral Concentrate (Roxanol) 20 MG/ML",
        "aliases": ["morphine", "morphine sulfate", "roxanol", "ms concentrate", "msir", "morphine concentrate"],
        "strength": "20MG/ML",
        "route": "Sublingual",
        "recommended_dosing": "0.25 mL (5 mg) SL q1-2h PRN pain/dyspnea; titrate per response — comfort-kit standard.",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Lorazepam",
        "brand_name": "Ativan",
        "name": "Lorazepam (Ativan) Concentrate 2 MG/ML",
        "aliases": ["lorazepam", "ativan"],
        "strength": "2MG/ML",
        "route": "Sublingual",
        "recommended_dosing": "0.25-1 mL (0.5-2 mg) SL q4-6h PRN anxiety/agitation.",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Haloperidol",
        "brand_name": "Haldol",
        "name": "Haloperidol (Haldol) Concentrate 2 MG/ML",
        "aliases": ["haloperidol", "haldol"],
        "strength": "2MG/ML",
        "route": "Sublingual",
        "recommended_dosing": "0.25-1 mL (0.5-2 mg) SL q6-8h PRN nausea/agitation/terminal delirium.",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Acetaminophen",
        "brand_name": "Tylenol",
        "name": "Acetaminophen Rectal Suppository 650 MG",
        "aliases": ["acetaminophen", "tylenol"],
        "strength": "650MG",
        "route": "Rectal",
        "recommended_dosing": "650 mg PR q4-6h PRN pain/fever — max 3-4 g/24h (reduce max in hepatic impairment).",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Atropine Sulfate",
        "brand_name": "Atropine Care",
        "name": "Atropine Sulfate Ophthalmic Solution 1% (used sublingually)",
        "aliases": ["atropine", "atropine care", "atropine 1%"],
        "strength": "1%",
        "route": "Sublingual",
        "recommended_dosing": "1-2 drops SL q4h PRN excessive oral/respiratory secretions (\"death rattle\").",
        "relative_cost_rank": 2,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Bisacodyl",
        "brand_name": "Dulcolax",
        "name": "Bisacodyl Rectal Suppository 10 MG",
        "aliases": ["bisacodyl", "dulcolax"],
        "strength": "10MG",
        "route": "Rectal",
        "recommended_dosing": "10 mg PR daily PRN constipation.",
        "relative_cost_rank": 2,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Ipratropium-Albuterol",
        "brand_name": "Duoneb",
        "name": "Duoneb (Ipratropium-Albuterol) 3 MG-0.5 MG/3 ML Inhalation Solution",
        "aliases": ["duoneb", "ipratropium albuterol", "ipratropium-albuterol"],
        "strength": "3MG-0.5MG/3ML",
        "route": "Inhalation",
        "recommended_dosing": "1 vial nebulized q4-6h PRN dyspnea/wheezing.",
        "relative_cost_rank": 2,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Ondansetron",
        "brand_name": "Zofran",
        "name": "Ondansetron ODT (Zofran) 4 MG Orally Disintegrating Tablet",
        "aliases": ["ondansetron", "zofran", "zofran odt"],
        "strength": "4MG",
        "route": "Sublingual",
        "recommended_dosing": "4 mg ODT SL/PO q8h PRN nausea/vomiting — max 3 doses/24h.",
        "relative_cost_rank": 2,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Hydromorphone",
        "brand_name": "Dilaudid",
        "name": "Hydromorphone (Dilaudid) Oral Solution 1 MG/ML",
        "aliases": ["hydromorphone", "dilaudid"],
        "strength": "1MG/ML",
        "route": "Sublingual",
        "recommended_dosing": "0.5-1 mg (0.5-1 mL) SL q3-4h PRN pain — alternative for morphine-intolerant patients.",
        "relative_cost_rank": 3,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Sennosides",
        "brand_name": "Senokot",
        "name": "Senna Tablet 8.6 MG",
        "aliases": ["senna", "sennosides", "senokot"],
        "strength": "8.6MG",
        "route": "PO",
        "recommended_dosing": "1-2 tabs PO BID PRN/scheduled for opioid-induced constipation prophylaxis.",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Docusate Sodium",
        "brand_name": "Colace",
        "name": "Docusate Sodium (Colace) Capsule 100 MG",
        "aliases": ["docusate", "colace"],
        "strength": "100MG",
        "route": "PO",
        "recommended_dosing": "100 mg PO BID for stool softening (often paired with a stimulant laxative).",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Furosemide",
        "brand_name": "Lasix",
        "name": "Furosemide (Lasix) Tablet 20 MG",
        "aliases": ["furosemide", "lasix"],
        "strength": "20MG",
        "route": "PO",
        "recommended_dosing": "20-40 mg PO daily PRN/scheduled for fluid overload/CHF symptom management.",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
    {
        "generic_name": "Oxygen",
        "brand_name": None,
        "name": "Oxygen Inhalation (2-5 LPM, titrate to SpO2)",
        "aliases": ["oxygen", "o2"],
        "strength": None,
        "route": "Inhalation",
        "recommended_dosing": "2-5 LPM via NC, titrate to comfort/SpO2 — not curative, symptom relief only.",
        "relative_cost_rank": 1,
        "pharmacy_available": True,
    },
]


def lookup_stock_matches(query: str) -> list[dict]:
    """Return stock formulary entries whose name, generic, brand, or an alias
    contains `query` — so typing either the brand or generic name surfaces
    the same normalized stock entry."""
    q = (query or "").strip().lower()
    if len(q) < 3:
        return []
    matches = []
    for entry in HOSPICE_STOCK_FORMULARY:
        haystacks = [
            entry["name"].lower(),
            (entry.get("generic_name") or "").lower(),
            (entry.get("brand_name") or "").lower(),
            *[a.lower() for a in entry.get("aliases", [])],
        ]
        if any(h and (q in h or h in q) for h in haystacks):
            matches.append(entry)
    return matches


def find_stock_entry(drug_name: str) -> dict | None:
    """Return the single best-matching stock formulary entry for a drug name
    (generic or brand), or None if it isn't one of our curated stock meds."""
    matches = lookup_stock_matches(drug_name)
    return matches[0] if matches else None


def get_therapeutic_alternatives(drug_name: str) -> dict:
    """Return other stock formulary medications in the same drug class(es) as
    `drug_name`, cheapest-first (`relative_cost_rank` ascending), for the
    read-only "same therapeutic family" box in the medication typeahead.

    Also flags whether the queried medication itself is currently marked
    available in the pharmacy — if not, the alternatives list is the
    recommended substitute, still cheapest-first.
    """
    # Imported lazily to avoid a circular import (drug_safety_service already
    # imports from this module's sibling constants elsewhere in the app).
    from app.services.drug_safety_service import get_drug_classes

    entry = find_stock_entry(drug_name)
    target_generic = entry["generic_name"] if entry else drug_name
    target_classes = get_drug_classes(target_generic or "")

    if not target_classes:
        return {
            "drug_name": drug_name,
            "matched_generic_name": entry.get("generic_name") if entry else None,
            "pharmacy_available": entry.get("pharmacy_available") if entry else None,
            "classes": [],
            "alternatives": [],
        }

    alternatives = []
    for other in HOSPICE_STOCK_FORMULARY:
        if entry and other is entry:
            continue
        other_classes = get_drug_classes(other.get("generic_name") or "")
        if not other_classes & target_classes:
            continue
        alternatives.append({
            "name": other["name"],
            "generic_name": other.get("generic_name"),
            "brand_name": other.get("brand_name"),
            "strength": other.get("strength"),
            "route": other.get("route"),
            "recommended_dosing": other.get("recommended_dosing"),
            "relative_cost_rank": other.get("relative_cost_rank", 99),
            "pharmacy_available": other.get("pharmacy_available", True),
        })

    alternatives.sort(key=lambda a: (a["relative_cost_rank"], a["name"]))

    return {
        "drug_name": drug_name,
        "matched_generic_name": entry.get("generic_name") if entry else None,
        "pharmacy_available": entry.get("pharmacy_available") if entry else None,
        "classes": sorted(target_classes),
        "alternatives": alternatives,
    }

