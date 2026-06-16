
# SNS Hospice EMR — Subscription & Feature Flag Plan

## Purpose
Define how a single SNS Hospice EMR codebase delivers different functionality per tenant using **subscription tiers** and **feature flags**, without tenant-specific code.

---

## Core Principle
- One UI
- One codebase
- One compliance engine
- Behavioral differences controlled by configuration

---

## Subscription Tiers

### Starter
- Core clinical documentation
- Patient, visit, note management
- Compliance tracking (TRACKING ONLY)
- Basic reports
- No payroll
- No voice-to-documentation
- Manual IDG attendance and signing

### Pro
- Full compliance engine (tenant-configurable enforcement)
- Payroll module
- Advanced exports (ADR, survey, audits)
- Voice-to-documentation for visits (optional)
- IDG voice disabled by default
- Assisted IDG attendance/signing

### Enterprise
- Multi-tenant staff (one user, many agencies)
- Custom data retention policies
- External or internal billing configuration
- Owner-level analytics (optional)
- Voice-to-documentation fully configurable per module
- Auto IDG attendance and signing (policy-controlled)

---

## Feature Flags (Examples)

- voice.visit.enabled
- voice.idg.enabled
- payroll.enabled
- billing.mode = internal | external
- idg.auto_attendance
- idg.auto_sign
- analytics.owner_view

---

## Enforcement
- Subscription controls **availability**
- Tenant policy controls **behavior**
- Staff access controls **visibility**

---

## Non-Negotiables
- Tenant isolation always enforced
- Same UI across all tenants
- No tenant-specific code branches
