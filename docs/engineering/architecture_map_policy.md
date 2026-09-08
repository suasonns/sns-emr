# Architecture Map Policy (Discovery Documentation)

## Rule

Whenever a discovery cycle on a major clinical/workflow engine surfaces architectural findings —
root causes, required behaviors, rejected anti-patterns, compliance interpretations, or narrative/
generation rules — a permanent architecture map markdown file MUST be created or updated in
`docs/clinical/` (or the most relevant existing docs subfolder for non-clinical engines) **before**
further implementation work continues on that engine.

Chat/session history is never an acceptable substitute for this document. An engineer six months
from now must be able to read one file and understand why the system works the way it does,
without reconstructing it from prior conversations.

## Scope

This applies to any of the following engines/workflows (and any future engine of comparable
complexity):

- RNICA narrative generation (`docs/clinical/rnica-architecture-map.md`)
- Documentation Insights
- LCD Support
- Evidence Harvester
- Recertification Reasoning Framework
- Plan of Care generation
- Certification Narratives
- Task Engine
- Benefit Period Logic

## Required contents

Each architecture map should cover, at minimum:

1. **Purpose** — what the system is, and what it is explicitly not.
2. **Regulatory foundation** — map each major requirement to its source (CMS Conditions of
   Participation, California hospice licensing regulations, LCD support expectations, etc.), with
   an explicit note that clause-level citations should be verified against the compliance team's
   authoritative source rather than treated as fixed once written.
3. **Goals** — the required objectives/behaviors, tied to the regulatory foundation above.
4. **Context/type framework** — if the system behaves differently per document/visit/record type,
   document each type's purpose, audience, style, included/excluded content.
5. **Workflow map** — the canonical reasoning/processing chain the output should follow, and why
   it became the core audit model.
6. **Domain-level detail** — expected behavior broken out by clinical or functional domain.
7. **Anti-patterns** — every rejected pattern discovered during development, and why it was
   rejected. This list must not shrink without an equivalent replacement justification recorded.
8. **Validation/authenticity test** — the permanent test used to judge whether output meets the
   bar, independent of any checklist.
9. **Resolved findings** — a durable record of defects discovered and fixed (root cause,
   resolution, how it was verified), so they are never re-discovered from scratch.
10. **Open gaps** — the active roadmap of known incomplete items, kept current as items resolve.
11. **Change control requirement** — the process contract for future modifications (see below).
12. **Discovery log** — a chronological, append-only history of major discoveries: date, finding,
    impact, decision, alternatives considered, status, and reference section. The architecture
    map documents current state; the discovery log documents how that state came to be, so a
    future engineer can answer "why does this rule exist" without searching chat history or
    tickets. Entries are appended, never rewritten or deleted — a superseded decision gets a new
    entry referencing the old one.
13. **Test patient registry** — the reference test patients, scenarios, and validation datasets
    used to discover and validate the engine's behavior (purpose, what each one validates, and
    where relevant, its ID). These are regression-test assets, not documentation templates or
    examples to imitate — a future developer should be able to answer "why do we keep this
    patient/scenario around?" from this section alone.
14. **Regression test matrix** — each major discovery converted into a repeatable check (rule,
    validation patient, expected result, verification method) so future changes can be validated
    against what was already learned instead of silently regressing it. The architecture map
    explains why a rule exists; this matrix verifies the rule still holds.

## Process

- Update the architecture map in the same change that introduces the discovery — not as
  follow-up cleanup.
- When an open gap is resolved, move it out of the "Open Gaps" section into "Resolved Findings"
  and fold the resolution into the relevant section above; do not simply delete it.
- New engines reaching a comparable level of discovery/complexity should get their own map file
  following this same structure.

## Change control requirement (applies to every engine covered by this policy)

Any future modification to a system with an architecture map must:

1. Review the architecture map first — check for conflicts with resolved findings or established
   anti-patterns before implementing a change.
2. Update the architecture map when discovery occurs, in the same change — including a new
   Discovery Log entry for any finding significant enough to change behavior.
3. Reference the architecture map in the PR description — state which sections were consulted and
   which were updated.
4. Record new findings (resolved or open) before the change is considered complete, in both the
   relevant content section and the Discovery Log.

See `docs/clinical/rnica-architecture-map.md` for the reference implementation of this policy.
