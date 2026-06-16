# Non-Negotiable Compliance Constraints

## Admission / Tasks
- INITIAL_RN_ICA and NOE_DUE are unique per patient
- Do NOT allow duplicates, even historically
- Status must be PENDING when created

## SOC
- SOC is immutable once set
- Re-authorization must be a no-op
- Never throw on SOC mismatch (survey risk)

## ADR Audit
- Must fail closed
- F1 emitted on any schema/query failure
- A2 emitted when adr_start > adr_end
