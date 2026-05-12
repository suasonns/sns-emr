# SNS EMR Documentation Diff Report

## Scope
This report compares **existing SNS EMR documentation** with the **newly generated Role & File-Visibility updates**.

---

## 1. SNS_EMR_MASTER_BLUEPRINT (1).md → SNS_EMR_MASTER_BLUEPRINT.md

### ✅ Newly Added Section
**Roles & Tenant Authority Model (LOCKED)**

**Additions:**
- Explicit separation of roles:
  - Owner Super User
  - Tenant Super User (subscription-gated)
  - Tenant Admin
  - Clinical Staff
- Hard rule: *Files are visible ONLY through a patient chart*
- Explicit prohibition of global or tenant-level file browsing

**Previous State:**
- Tenant isolation described at a high level
- Roles not formally differentiated
- File visibility rules implied but not stated

---

## 2. NEW: SNS_EMR_Role_Matrix.md

### ✅ New Canonical Document

**Purpose:**
- Single authoritative definition of all system roles
- Designed to be referenced by other *.md files

**New Content Introduced:**
- Global file visibility rule
- Role-by-role scope definitions
- Clear Owner vs Tenant hierarchy

---

## 3. NEW: SNS_EMR_Definition_of_Done_Role_Addendum.md

### ✅ New Go/No-Go Enforcement Addendum

**Purpose:**
- Extends "Global Requirements (ALL GATES)"

**New Non-Negotiables Added:**
- Role separation enforced
- Tenant Super User is tenant-scoped and optional
- Absolute patient-only file visibility
- No global or tenant-level files list

---

## Impact Summary

| Area | Before | After |
|-----|-------|------|
| Role clarity | Implicit | Explicit, locked |
| Tenant super user | Undefined | Defined + gated |
| Owner vs tenant separation | Implicit | Explicit |
| File visibility rule | Implied | Explicit + enforced |
| Survey defensibility | Good | Strong |

---

## Conclusion
These updates **do not change system scope**.
They:
- Remove ambiguity
- Align documentation with actual security intent
- Prevent future regressions during subscription-tier design

✅ Safe to merge
✅ No backward incompatibility
