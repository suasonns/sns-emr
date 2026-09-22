# SNS Hospice Solutions — Copilot Instructions

This repository is governed by the **SNS Repository-First Implementation Constitution**:

`docs/development/SNS_REPOSITORY_FIRST_IMPLEMENTATION_CONSTITUTION.md`

Read the full constitution before starting any SNS Hospice Solutions work (RNICA, Patient Chart, HOPE, Owner/Tenant/Biller Platform, Orders, Plan of Care, certifications, and all related services/UI). Do not summarize from memory — open and read the file each session.

## Non-negotiable rules (see the constitution for full detail)

1. **Repository-first.** Inspect the current repo (branch, git status, existing implementation, existing tests, existing authority docs) before any recommendation or change. Prior conversation/session memory is never authoritative on its own.
2. **Mandatory session-start gate.** Every session must produce the session-start response defined in the constitution's Section 18 before any file is modified.
3. **No-assumption rule.** Never assume a feature/field/component/API/test is missing or present — classify as VERIFIED / PARTIAL / NOT VERIFIED / CONFLICTING / NOT FOUND / SUPERSEDED only after searching.
4. **Reuse before create.** Search for an existing component/hook/utility/route/token before creating a new one.
5. **RNICA preservation.** RNICA redesign changes presentation/navigation/usability only — never clinical fields, validation, response values, HOPE/ACP logic, autosave, readiness, lock, amendments, or audit behavior, unless an approved defect requires it.
6. **shadcn/ui is a primitive toolkit only**, restyled to SNS's existing theme tokens — never shadcn templates, dashboards, or generated layouts, and never a competing design system.
7. **Four-mode visual verification** (Desktop Light, Desktop Dark, Mobile Light, Mobile Dark) is required before any redesigned screen is called complete. Source/DOM inspection alone is not visual verification.
8. **Implementation over reporting.** If authority docs/plans already exist, implement — do not produce another gap report/roadmap/audit unless explicitly requested or a real conflict/blocker exists.
9. **Stop immediately** on any data-integrity risk (duplicate records, cross-patient/cross-tenant data, lock bypass, audit/signature loss, etc.) and report before continuing.

If any part of this file conflicts with the full constitution, the constitution controls.
