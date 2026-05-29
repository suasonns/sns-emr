\# SNS EMR – Compliance Guard \& Core Rules Mapping (ANTI‑DRIFT)



\---

SNS EMR COMPLIANCE NOTICE



This file governs system behavior through reference to:



/docs/compliance/core\_rules.md



If any service, module, or implementation conflicts with core\_rules.md,

the implementation MUST be changed.



core\_rules.md is the single source of truth.

\---



\## PURPOSE OF THIS FILE



This document:

\- Does NOT redefine rules

\- Does NOT introduce new behavior

\- DOES enforce alignment between:

&#x20; - core\_rules.md

&#x20; - system services

&#x20; - enforcement logic

\- EXISTS to prevent architectural and compliance drift



\---



\## GOVERNANCE



\*\*Governed by:\*\*  

`/docs/compliance/core\_rules.md`



\*\*Scope of Enforcement:\*\*

\- Visit classification

\- Discipline scope

\- RN authority

\- Task creation and completion

\- Discharge for Cause (DFC)

\- Audit and finalization rules

\- Administrative (QAPI) vs clinical separation



No service may exceed, weaken, or reinterpret defined scope.



\---



\## COMPLIANCE CHECKLIST (REQUIRED FOR ANY CHANGE)



Before merging any change touching visits, notes, tasks, RN logic, discharge, or scope:



\- \[ ] Reviewed against `/docs/compliance/core\_rules.md`

\- \[ ] RN scope not weakened

\- \[ ] Telephone ≠ visit rule preserved

\- \[ ] Administrative visits not treated as clinical

\- \[ ] No discipline scope expansion

\- \[ ] Task evidence requirements preserved

\- \[ ] Audit fields enforced

\- \[ ] QAPI visits excluded from clinical metrics



If any item fails, the change is non‑compliant.



\---



\## ASSERTION CONTRACT (CONCEPTUAL)



```python

def assert\_core\_rules():

&#x20;   """

&#x20;   All logic governed by this file assumes compliance with

&#x20;   /docs/compliance/core\_rules.md.



&#x20;   If this assertion is violated, the implementation is non‑compliant.

&#x20;   """

&#x20;   return True

