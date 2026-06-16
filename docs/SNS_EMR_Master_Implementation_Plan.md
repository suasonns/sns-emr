
# SNS Hospice EMR — Master Implementation Plan

## Phase 1 — Tenant Hardening
- tenant_id enforced on all core tables
- Backfill verification
- Cross-tenant isolation
- Safe create/delete post-hardening

## Phase 2 — User ↔ Tenant Model
- user_tenants join table
- Per-tenant role, discipline, staff type, access level
- Tenant selection after login
- Per-tenant suspension

## Phase 3 — Access & Subscription Engine
- ADMIN / STAFF / READ_ONLY
- Feature availability via subscription
- Same UI, different enabled modules

## Phase 4 — Credential & Compliance Engine
- Credential catalog
- Tenant-configurable enforcement
- Alert escalation
- HR override modes

## Phase 5 — Sensitive HR Modernization
- SSN encrypted + masked
- I-9, W-4, contracts as documents
- Tenant chooses ENFORCED / TRACKING / EXTERNAL

## Phase 6 — Clinical Implementation
- Visits
- Notes
- IDG
- POC
- ADR exports

## Rule
Clinical workflows only begin after Phases 1–5 are locked.
