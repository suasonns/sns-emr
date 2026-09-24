# RBAC Validation

Evidence below is based on direct reading of the recovered code in `backend/app/api/owner_admin.py`, `backend/app/core/role_guards.py`, `backend/app/core/roles.py`, `backend/app/core/account_types.py`, `backend/app/core/protected_tenants.py`, `backend/app/core/auth.py`, `backend/app/models/staff_permission_grant.py`, `backend/app/services/admin_bootstrap_service.py`, and the recovered backend tests.

## 1. Multi-tenant isolation still preserved — **PASS**

**Why:** the recovered staff-management surface is explicitly scoped to SNS platform staff, not arbitrary tenant users.

**Code evidence**

- `backend/app/api/owner_admin.py:336` defines `_is_platform_staff_account()` and documents that role membership in `PLATFORM_ROLES` is the authoritative isolation boundary.
- `backend/app/api/owner_admin.py:985` (`list_platform_users`) filters by `u.role = ANY(:platform_roles)` and the docstring says the surface is “hard-scoped to PLATFORM_ROLES so no tenant-agency or biller account is ever returned.”
- `backend/app/api/owner_admin.py:2088` (`create_platform_staff`) hardcodes `tenant_id=PLATFORM_TENANT_ID` when creating SNS staff, preventing accidental creation under arbitrary tenant rows.
- `backend/app/core/protected_tenants.py:26` defines `PLATFORM_TENANT_ID`, the canonical SNS platform tenant UUID used by the staff-management flow.
- `backend/app/models/user.py:16` keeps `tenant_id` required/non-null with FK restriction; the recovery extends the model but does not relax tenant linkage.

**Test evidence**

- `backend/tests/test_owner_platform_rbac_matrix.py:153` (`test_tenant_and_biller_roles_never_get_staff_capabilities`) asserts tenant/biller roles get nothing from the `staff.*` matrix.
- `backend/tests/test_owner_platform_staff_profile.py:222` (`test_get_platform_staff_detail_404_for_tenant_user`) persists a tenant `ADMINISTRATOR` row and verifies `GET /api/owner/users/{id}` returns `404`.

## 2. Platform Owner remains highest role — **PASS**

**Why:** OWNER still receives unconditional `staff.*` authority and retains exclusive ownership-assignment power.

**Code evidence**

- `backend/app/core/roles.py:298` defines the authoritative `STAFF_CAPABILITIES` set.
- `backend/app/core/roles.py:325-405` defines `PLATFORM_PERMISSION_MATRIX`, but the comment immediately above `_role_grants()` says OWNER is intentionally omitted because it always gets every `staff.*` capability.
- `backend/app/core/roles.py:418` (`effective_capabilities_for_role`) returns `set(STAFF_CAPABILITIES)` for OWNER.
- `backend/app/core/roles.py:452` (`role_can`) short-circuits `if normalized_actor == "OWNER": return True` before other restrictions.
- `backend/app/api/owner_admin.py:2330` (`update_platform_staff_role`) separately enforces `if payload.role == "OWNER" and not role_can(user.role, "staff.assign_owner_role")`, keeping owner assignment exclusive.

**Test evidence**

- `backend/tests/test_owner_platform_rbac_matrix.py:31` (`test_owner_has_every_staff_capability`) iterates all recovered `staff.*` capabilities and expects `role_can("OWNER", capability) is True`.
- `backend/tests/test_owner_platform_rbac_matrix.py:126` (`test_no_non_owner_role_can_ever_assign_owner_role`) verifies every non-owner platform role is denied `staff.assign_owner_role`.

## 3. Tenant users cannot access owner functions — **PASS**

**Why:** both backend and frontend gate owner access to platform-scope actors.

**Code evidence**

- `backend/app/core/role_guards.py:48` (`require_platform_permission`) first rejects non-platform roles with `detail="Platform staff access required"` and then rejects missing capability holders.
- `backend/app/core/roles.py:452` (`role_can`) returns `False` when `not is_platform_role(normalized_actor)`.
- `backend/app/core/auth.py:20` expands `VALID_ROLES`, but only valid roles can authenticate; that does not bypass the platform-only checks above.
- `sns-emr-frontend/src/utils/authorization.ts:14-26` changed owner-route access to `user.access_scope === "platform"`, not tenant scope.

**Test evidence**

- `backend/tests/test_owner_platform_rbac_matrix.py:153` proves tenant/biller roles (`ADMINISTRATOR`, `DPCS`, `RN`, `BILLING`, `CFO`) cannot even get `staff.view`.
- `backend/tests/test_owner_platform_rbac_matrix.py:187` (`test_dependency_denies_non_platform_role`) calls `require_platform_permission("staff.view")` with `ADMINISTRATOR` and expects `403`.
- `backend/tests/test_owner_platform_staff_profile.py:182` (`test_create_rejects_invalid_role`) rejects tenant role `ADMINISTRATOR` when attempting to create platform staff.

## 4. Permission system remains role-driven — **PASS**

**Why:** the recovered code repeatedly states and enforces that department/job title/account type/access-level labels do not grant permissions; permissions come from roles plus explicit delegated grants.

**Code evidence**

- `backend/app/core/roles.py:325-405` is the authoritative permission map (`PLATFORM_PERMISSION_MATRIX`).
- `backend/app/core/roles.py:441` (`capabilities_for_role`) says it exposes the same source of truth `role_can()` enforces server-side.
- `backend/app/core/departments.py` module docstring says department “grants NO permissions.”
- `backend/app/core/job_titles.py` module docstring says job title is “presentational/organizational only” and authorization always flows through `role_can()` / `PLATFORM_PERMISSION_MATRIX`.
- `backend/app/core/account_types.py` only validates identity type labels; it does not assign capabilities.
- `backend/app/api/owner_admin.py:1134-1166` computes per-row `allowed_actions` by calling `role_can(...)` on the backend rather than trusting UI labels.

**Test evidence**

- `backend/tests/test_owner_platform_rbac_matrix.py` as a whole is built around `role_can()` rather than department/account-type checks.
- `backend/tests/test_owner_platform_staff_lifecycle.py:190` (`test_list_rows_include_allowed_actions_and_actor_capabilities`) asserts the API returns `actor_capabilities` and `allowed_actions`, i.e. server-derived permission data.

## 5. Audit logging captures security events — **PASS**

**Why:** security-relevant state changes log explicit audit actions and the recovered audit API preserves severity/affected-permissions metadata.

**Code evidence**

- `backend/app/api/owner_admin.py:1352` (`set_platform_staff_status`) writes `_STATUS_AUDIT_ACTION[payload.status]` with prior/new status and reason.
- `backend/app/api/owner_admin.py:1425` (`revoke_platform_staff_access`) logs `OWNER_REVOKED_STAFF_ACCESS`.
- `backend/app/api/owner_admin.py:1489` (`remove_platform_staff`) logs `OWNER_REMOVED_STAFF` plus reason.
- `backend/app/api/owner_admin.py:2311` (`update_platform_staff_role`) logs `OWNER_CHANGED_STAFF_ROLE` with `previous_role` and `new_role`.
- `backend/app/api/owner_admin.py:159` (`_severity_for_event`) centralizes risk classification, including CRITICAL owner/tenant-status changes and HIGH revoke/remove cases.

**Test evidence**

- `backend/tests/test_owner_platform_staff_delegation.py:180` (`test_revoke_access_transitions_to_disabled_with_distinct_audit_event`) checks that `OWNER_REVOKED_STAFF_ACCESS` appears in audit history.
- `backend/tests/test_owner_platform_staff_lifecycle.py:366` (`test_role_change_is_audited`) verifies an `OWNER_CHANGED_STAFF_ROLE` row is written with correct metadata.
- `backend/tests/test_owner_audit_logs.py:271` (`test_audit_logs_role_change_event_carries_severity_and_affected_permissions`) verifies `severity` and `affected_permissions` survive end-to-end through `GET /api/owner/audit-logs`.

## 6. No direct privilege escalation path — **PASS**

**Why:** self-promotion, owner-role delegation, and over-ceiling changes are all blocked in the recovered code.

**Code evidence**

- `backend/app/api/owner_admin.py:2311` (`update_platform_staff_role`) blocks self-role changes: `if target.id == user.user_id: ... "You cannot change your own platform role."`
- The same function blocks non-owner assignment of OWNER and prevents demoting the final active owner.
- `backend/app/core/roles.py:406` marks `staff.assign_owner_role` as non-delegable.
- `backend/app/core/roles.py:514` (`can_delegate_capability`) only allows delegation when the actor already holds the capability and when it is not in `NON_DELEGABLE_CAPABILITIES`.
- `backend/app/core/roles.py:452` (`role_can`) blocks action on OWNER targets and lateral PLATFORM_ADMIN mutation for non-owners.

**Test evidence**

- `backend/tests/test_owner_platform_staff_lifecycle.py:311` (`test_only_owner_may_assign_owner_role`) expects `403` for a platform admin promoting someone to OWNER.
- `backend/tests/test_owner_platform_staff_lifecycle.py:323` (`test_actor_cannot_change_own_role`) expects `403` for self-role change.
- `backend/tests/test_owner_platform_staff_delegation.py:314` (`test_admin_cannot_delegate_a_capability_it_does_not_hold`) verifies a platform admin cannot delegate `staff.assign_owner_role`.
- `backend/tests/test_owner_platform_rbac_matrix.py:133` (`test_no_non_owner_role_can_ever_mutate_an_owner_target`) covers suspend/disable/revoke/remove against OWNER targets.

## 7. Owner permissions are not hardcoded — **FAIL**

**Why:** the recovered implementation still hardcodes OWNER as a superuser for the `staff.*` namespace.

**Evidence of hardcoding**

- `backend/app/core/roles.py` explicitly comments that OWNER is “intentionally not listed” in `PLATFORM_PERMISSION_MATRIX` because it always gets every `staff.*` capability.
- `backend/app/core/roles.py:418` (`effective_capabilities_for_role`) returns `set(STAFF_CAPABILITIES)` for OWNER.
- `backend/app/core/roles.py:452` (`role_can`) short-circuits with `if normalized_actor == "OWNER": return True`.
- `backend/app/core/role_guards.py:15` keeps explicit `require_owner()` for owner-only routes.

**Interpretation:** frontend button logic is not hardcoded — it relies on backend `actor_capabilities` and `allowed_actions` — but OWNER’s backend authority is still hardcoded as an unconditional superuser grant rather than being read from a database table or configurable permission matrix.

## 8. Permission grants remain database-driven — **PASS**

**Why:** delegated grants live in a dedicated table/model and are unioned into effective permissions at request time.

**Code evidence**

- `backend/app/models/staff_permission_grant.py:28-61` defines the persisted grant record with `target_user_id`, `capability`, grantor, timestamps, expiration, and revocation metadata.
- `backend/app/api/owner_admin.py:1849` (`_active_grants_query`) reads active rows from the database; `1853` filters out revoked/expired rows.
- `backend/app/api/owner_admin.py:1612` (`get_platform_staff_permissions`) returns role defaults, delegated grants, and effective permissions based on database rows.
- `backend/app/core/roles.py:418` (`effective_capabilities_for_role`) unions `direct_grants` into the role-default set.

**Test evidence**

- `backend/tests/test_owner_platform_staff_delegation.py:274` (`test_admin_can_delegate_a_capability_it_holds`) creates a grant, verifies it appears in `effective_permissions`, then revokes it and verifies it disappears.
- `backend/tests/test_owner_platform_staff_delegation.py:325` (`test_delegated_capability_grants_real_effective_access`) proves a delegated `staff.suspend` grant changes real endpoint access, not just UI state.

## Bottom line

The recovered RBAC work **does** preserve tenant/platform separation, owner primacy, backend-enforced role-driven permissions, auditable security events, and database-backed delegated grants. The one clear caveat is that **OWNER authority is still hardcoded** as an unconditional superuser path for `staff.*`, so item 7 fails if the requirement is “no hardcoded owner superuser logic.”
