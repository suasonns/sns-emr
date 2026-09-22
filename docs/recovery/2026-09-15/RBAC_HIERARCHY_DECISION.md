# RBAC Hierarchy Decision

Read-only. No implementation. Awaiting approval before any code change.

## A. Existing recovered hierarchy (as implemented in `roles.py::ACCESS_LEVEL_FOR_ROLE`)

```
1. Owner
2. Administrator
3. Security | Compliance | Billing | AI Management        (tied, same tier)
4. Operations | Developer | DevOps | Implementation | QA  (tied, same tier)
5. Support | Customer Service                             (tied, same tier)
6. Auditor
```

## B. Former proposed hierarchy (as stated in the task)

```
Platform Owner
Platform Administrator
Customer Service
Support
Developer
```

## C. Permission differences

| Role | Recovered tier | Proposed tier | Recovered `staff.*` grants | Consistent with proposed ranking? |
|---|---|---|---|---|
| Owner | 1 | 1 | all (unconditional) | ✅ match |
| Platform Administrator | 2 | 2 | full operational set (all but assign_owner_role / OWNER+PLATFORM_ADMIN targets) | ✅ match |
| Customer Service | 5 | 3 | **none** (empty capability set) | ❌ mismatch — proposed ranks it 3rd (above Support and Developer); recovered gives it the *fewest* capabilities of any platform role |
| Support | 5 | 4 | view, reset_password | ❌ mismatch — proposed ranks it 4th (above Developer); recovered ties it with Customer Service at tier 5, one level *below* Developer's tier 4 |
| Developer | 4 | 5 | view only | ❌ mismatch — proposed ranks it last (5th); recovered places it at tier 4, *above* both Support and Customer Service |

**Net effect:** the recovered code and the proposed hierarchy agree on Owner and Administrator,
but invert the relative ranking of Developer versus Support/Customer Service. Recovered treats
Developer as more privileged (tier 4, `staff.view`) than Support/Customer Service (tier 5,
`staff.view`+`reset_password` for Support, nothing for Customer Service) — the proposed hierarchy
wants the reverse.

## D. Security implications

- **If the recovered ordering ships as-is:** Developer accounts would sit above Customer
  Service/Support in nominal tier — but note the *actual* capability grants don't create a
  privilege-escalation risk either way, since Developer's only capability is `staff.view` (read
  metadata), strictly less than Support's `staff.view + staff.reset_password`. The "tier number"
  is a display/derived label (`access_level_for_role`, explicitly documented as "presentational
  only" in the code) — it does not by itself grant anything. The real authorization surface is
  `PLATFORM_PERMISSION_MATRIX`, which is already least-privilege for Developer.
- **If the proposed ordering is adopted and capabilities are reshuffled to match it** (e.g. giving
  Customer Service and/or Support more capabilities than Developer, or elevating their access
  tier above Developer's), that would be a **net capability increase** for two currently
  minimally-privileged support-facing roles — this should go through the same least-privilege
  review as any other capability grant, not be treated as a cosmetic relabel.
- **Risk of doing nothing:** low. The mismatch is currently a labeling/display inconsistency
  versus a stated intent, not an active vulnerability — Customer Service already has zero
  capabilities and Support has the minimum needed for its stated job function (password reset).

## E. Recommended final hierarchy

This review does not have authority to decide the business-intended ordering and does not
recommend one hierarchy over the other unilaterally. Two paths, both requiring explicit approval:

1. **Adopt the recovered hierarchy** (Owner > Admin > Security/Compliance/Billing/AI >
   Operations/Developer/DevOps/Implementation/QA > Support/Customer Service > Auditor) as final —
   requires confirming this was the actual intended design and that the "former proposed"
   hierarchy in the task was outdated/approximate.
2. **Adopt the proposed hierarchy** (Owner > Admin > Customer Service > Support > Developer) as
   final — requires: (a) deciding where Security/Compliance/Billing/AI/Operations/DevOps/
   Implementation/QA/Auditor fit relative to Customer Service/Support/Developer (the proposed
   list only names 5 of the 13 recovered roles), and (b) a deliberate capability-grant decision
   for whether Customer Service/Support should gain capabilities currently reserved for
   higher-tier roles, or whether only the display tier changes while capabilities stay as-is.

**No `ACCESS_LEVEL_FOR_ROLE` or `PLATFORM_PERMISSION_MATRIX` change has been made.** Awaiting
approval of option 1 or 2 (or a corrected option 3) before any implementation proceeds.
