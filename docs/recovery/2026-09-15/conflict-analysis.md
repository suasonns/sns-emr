# Conflict Analysis

Classification key:

- **A. NO CONFLICT** — file exists only in recovery; no current-main counterpart.
- **B. LOW CONFLICT** — file exists on `main`, but the recovered change is small or cleanly additive/non-overlapping.
- **C. MEDIUM CONFLICT** — file exists on `main` and the recovered change is additive but touches core behavior or adjacent logic that still needs human merge review.
- **D. HIGH CONFLICT** — file exists on `main` and the recovered content substantially rewrites the same surface, so taking it wholesale risks overwriting current-main intent.

## File-by-file classification

| Path | Class | Rationale |
|---|---|---|
| `.github/copilot-instructions.md` | A | New operational instructions file; absent on current `main`. |
| `backend/alembic/versions/um2a1c2c3o5u6_add_account_type_to_users.py` | A | New migration; absent on current `main`. |
| `backend/alembic/versions/um2b1c2c3o5u7_add_identity_fields_to_users.py` | A | New migration; absent on current `main`. |
| `backend/alembic/versions/um2c1c2c3o5u8_add_platform_to_users.py` | A | New migration; absent on current `main`. |
| `backend/alembic/versions/um2d1c2c3o5u9_add_staff_status_and_permission_grants.py` | A | New migration; absent on current `main`. |
| `backend/alembic/versions/um2s1a2f3f4b5_add_department_notes_updated_by_to_users.py` | A | New migration; absent on current `main`. |
| `backend/app/api/owner_admin.py` | D | Same file on `main`, but recovery rewrites the user-management/audit portions into platform-staff-specific RBAC, adds many new endpoints, and changes existing payloads. |
| `backend/app/core/account_types.py` | A | New taxonomy module; absent on current `main`. |
| `backend/app/core/auth.py` | B | Existing file on `main`; recovered change is a single additive expansion of `VALID_ROLES`. |
| `backend/app/core/departments.py` | A | New taxonomy module; absent on current `main`. |
| `backend/app/core/job_titles.py` | A | New taxonomy module; absent on current `main`. |
| `backend/app/core/platforms.py` | A | New platform-catalog module; absent on current `main`. |
| `backend/app/core/protected_tenants.py` | B | Existing file on `main`; recovered change introduces a named `PLATFORM_TENANT_ID` constant and reuses it in the protected set. |
| `backend/app/core/role_guards.py` | B | Existing file on `main`; recovered change is additive (`require_platform_permission`) and does not rewrite `require_owner`. |
| `backend/app/core/roles.py` | C | Existing file on `main`; recovered change is largely additive, but it extends platform-role definitions and adds a new staff-permission engine in a security-critical module. |
| `backend/app/models/__init__.py` | B | Existing file on `main`; recovered change is a small additive model import for `StaffPermissionGrant`. |
| `backend/app/models/staff_permission_grant.py` | A | New model file; absent on current `main`. |
| `backend/app/models/user.py` | C | Existing file on `main`; recovered change is additive, but it extends the core `User` schema with multiple staff-management fields that must stay aligned with migrations and API behavior. |
| `backend/app/services/admin_bootstrap_service.py` | B | Existing file on `main`; recovered change is a one-line branding/name adjustment for the seeded OWNER identity. |
| `backend/tests/test_owner_audit_logs.py` | A | New backend test file; absent on current `main`. |
| `backend/tests/test_owner_platform_rbac_matrix.py` | A | New backend test file; absent on current `main`. |
| `backend/tests/test_owner_platform_staff_delegation.py` | A | New backend test file; absent on current `main`. |
| `backend/tests/test_owner_platform_staff_lifecycle.py` | A | New backend test file; absent on current `main`. |
| `backend/tests/test_owner_platform_staff_profile.py` | A | New backend test file; absent on current `main`. |
| `backend/tests/test_treatment_identity_migration.py` | B | Existing file on `main`; recovered change is a one-line `HEAD_REVISION` update. |
| `docs/PLATFORM_ARCHITECTURE_ROADMAP.md` | A | New documentation file; absent on current `main`. |
| `docs/SNS_STAFF_ACCESS_CHECKPOINT.md` | A | New documentation file; absent on current `main`. |
| `sns-emr-frontend/public/brand/sns-logo-dark.svg` | B | Existing asset on `main`; recovered change swaps artwork but does not alter app logic. |
| `sns-emr-frontend/public/brand/sns-logo-icon-dark-tile.svg` | A | New asset; absent on current `main`. |
| `sns-emr-frontend/public/brand/sns-logo-icon-dark.svg` | A | New asset; absent on current `main`. |
| `sns-emr-frontend/public/brand/sns-logo-icon.svg` | B | Existing asset on `main`; recovered change is visual-only. |
| `sns-emr-frontend/public/brand/sns-logo-light.svg` | B | Existing asset on `main`; recovered change is visual-only. |
| `sns-emr-frontend/src/App.tsx` | B | Existing router on `main`; recovered change only adds `SetPasswordPage` import and `/set-password` route. |
| `sns-emr-frontend/src/api/ownerAdmin.ts` | C | Existing owner API client on `main`; recovery adds many new contracts/endpoints and changes the staff/audit payload surface. |
| `sns-emr-frontend/src/components/BrandLogo.tsx` | B | Existing shared component on `main`; recovered change broadens variants and centralizes more assets without rewriting callers’ semantics. |
| `sns-emr-frontend/src/owner/OwnerDashboard.jsx` | C | Existing owner controller on `main`; recovery changes shelling, loading behavior, and delegated-staff access routing for `users`/`audit`. |
| `sns-emr-frontend/src/owner/accessLevels.js` | A | New frontend helper; absent on current `main`. |
| `sns-emr-frontend/src/owner/auditCategories.js` | A | New frontend helper; absent on current `main`. |
| `sns-emr-frontend/src/owner/components/AddStaffModal.jsx` | A | New frontend modal; absent on current `main`. |
| `sns-emr-frontend/src/owner/components/AuditEventDrawer.jsx` | A | New frontend drawer; absent on current `main`. |
| `sns-emr-frontend/src/owner/components/StaffProfileDrawer.jsx` | A | New frontend drawer; absent on current `main`. |
| `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` | D | Existing page on `main`; recovered version substantially expands it into a richer audit application with new filters, export, severity rendering, and drawer interactions. |
| `sns-emr-frontend/src/owner/pages/UserManagement.jsx` | D | Existing page on `main`; recovered version repurposes it from cross-tenant user listing to SNS Staff & Access with tabs, modals, drawers, and backend-driven RBAC actions. |
| `sns-emr-frontend/src/owner/shell/OwnerShell.jsx` | A | New shell component; absent on current `main`. |
| `sns-emr-frontend/src/pages/SetPasswordPage.tsx` | A | New route page; absent on current `main`. |
| `sns-emr-frontend/src/utils/authorization.ts` | C | Existing authorization helper on `main`; recovered change deliberately broadens owner-route entry to any platform-scope user and therefore needs security review with the backend RBAC change. |

## High-risk detailed comparisons

### `backend/app/core/auth.py` — classified **B / LOW CONFLICT**

- **Current main summary:** JWT auth dependency with `VALID_ROLES`, `CurrentUser`, and `get_current_user`; current main already knows legacy platform roles such as `OWNER`, `PLATFORM_SUPPORT`, `PLATFORM_BILLING`, `PLATFORM_OPERATIONS`, `PLATFORM_AI_MANAGEMENT`, and `PLATFORM_COMPLIANCE`.
- **Recovered summary:** same file structure, but `VALID_ROLES` now also includes the recovered SNS Staff & Access roles required by the new platform-staff UI and API (`PLATFORM_ADMIN`, `PLATFORM_SECURITY`, `PLATFORM_DEVELOPER`, `PLATFORM_DEVOPS`, `PLATFORM_IMPLEMENTATION`, `PLATFORM_CUSTOMER_SERVICE`, `PLATFORM_QA`, `PLATFORM_AUDITOR`).
- **Exact changed region:** one additive hunk at `@@ -69,6 +69,20 @@ VALID_ROLES = {` adding comments and the eight new role strings.
- **Key diff quote:**

  ```diff
  +    "PLATFORM_ADMIN",
  +    "PLATFORM_SECURITY",
  +    "PLATFORM_DEVELOPER",
  +    "PLATFORM_DEVOPS",
  +    "PLATFORM_IMPLEMENTATION",
  +    "PLATFORM_CUSTOMER_SERVICE",
  +    "PLATFORM_QA",
  +    "PLATFORM_AUDITOR",
  ```

- **Merge recommendation:** take the recovered hunk as-is if the recovered platform-staff RBAC work is adopted; there is no overlap with other logic in current main, and without this hunk any newly assigned platform-staff role would authenticate incorrectly.

### `backend/app/core/roles.py` — classified **C / MEDIUM CONFLICT**

- **Current main summary:** canonical role-alias module that already normalizes tenant/billing/platform roles, defines `PLATFORM_ROLES`, `CLINICAL_ADMIN_ROLES`, `FINANCIAL_ADMIN_ROLES`, `access_scope_for_role`, and `role_matches`, but does not yet have a dedicated `staff.*` permission engine for SNS Staff & Access.
- **Recovered summary:** preserves all current-main canonical logic and then adds the recovered platform-staff RBAC foundation: new platform role names, derived access-level display tiers, platform staff statuses, `STAFF_CAPABILITIES`, `PLATFORM_PERMISSION_MATRIX`, effective-capability union, target-role ceilings, and delegation rules.
- **Exact changed regions:** (1) `@@ -64,6 +64,22 @@ PLATFORM_ROLES = {` extends the platform catalog; (2) `@@ -223,3 +239,308 @@ def role_matches(` appends the new RBAC subsystem.
- **Key diff quotes:**

  ```diff
  +ACCESS_LEVEL_FOR_ROLE: dict[str, str] = {
  +    "OWNER": "LEVEL_1_OWNER",
  +    "PLATFORM_ADMIN": "LEVEL_2_ADMINISTRATOR",
  +    ...
  +}
  ```

  ```diff
  +STAFF_CAPABILITIES = {
  +    "staff.view",
  +    "staff.create",
  +    "staff.invite",
  +    ...
  +}
  ```

  ```diff
  +def role_can(...):
  +    if normalized_actor == "OWNER":
  +        return True
  +    ...
  +    if normalized_target == "OWNER" or capability == "staff.assign_owner_role":
  +        return False
  ```

- **Merge recommendation:** merge manually but keep the recovered RBAC block nearly wholesale; it is intentionally appended rather than interleaved, so the main integration risk is semantic review of the new permission model, not textual conflict with old code.

### `backend/app/core/role_guards.py` — classified **B / LOW CONFLICT**

- **Current main summary:** only defines `require_owner`, which returns the authenticated user or raises `403 Owner access required`.
- **Recovered summary:** leaves `require_owner` intact and adds `require_platform_permission(capability)` so non-owner platform roles can be admitted to staff-management endpoints only through `role_can`.
- **Exact changed regions:** `@@ -1,8 +1,10 @@` adds `Callable` and imports from `roles.py`; `@@ -27,4 +29,34 @@ def require_owner(...)` appends the new dependency.
- **Key diff quote:**

  ```diff
  +def require_platform_permission(capability: str) -> Callable[..., CurrentUser]:
  +    def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
  +        if not is_platform_role(user.role):
  +            raise HTTPException(..., detail="Platform staff access required")
  +        if not role_can(user.role, capability):
  +            raise HTTPException(..., detail=f"Missing required platform permission: {capability}")
  ```

- **Merge recommendation:** take recovered addition as-is if the staff RBAC system is retained; this is cleanly additive and centralizes access checks rather than duplicating them in each endpoint.

### `backend/app/core/protected_tenants.py` — classified **B / LOW CONFLICT**

- **Current main summary:** defines `PROTECTED_TENANT_IDS` inline and exposes `assert_not_protected` for cleanup/purge safety.
- **Recovered summary:** same behavior, but now introduces named `PLATFORM_TENANT_ID` and reuses it inside `PROTECTED_TENANT_IDS`, allowing other code to reference the SNS platform tenant safely.
- **Exact changed region:** `@@ -18,9 +18,16 @@` inserts the constant and replaces the literal in the protected set.
- **Key diff quote:**

  ```diff
  +PLATFORM_TENANT_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
  ...
  -        uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
  +        PLATFORM_TENANT_ID,
  ```

- **Merge recommendation:** take recovered hunk as-is; conflict risk is minimal and it removes a duplicated magic UUID.

### `backend/app/api/owner_admin.py` — classified **D / HIGH CONFLICT**

- **Current main summary:** owner-only platform API for tenant onboarding, tenant financials, platform-wide audit logs, a cross-tenant user roster (`/users`) with tenant filter and simple enable/disable/reset operations, plus system/adoption health endpoints.
- **Recovered summary:** keeps tenant onboarding/financial/system-health code, but rewrites the user-management surface into SNS Staff & Access for platform roles only, adds audit severity/request-id/entity filters, adds staff-profile CRUD, role changes, 4-state lifecycle, delegated-permission grants, and richer roster payloads (`access_level`, `allowed_actions`, `actor_capabilities`, departments/platforms/account types/job-title catalogs).
- **Exact changed regions:**
  1. `@@ -31,11 +31,30 @@` adds imports for `account_types`, `departments`, `job_titles`, `platforms`, `PLATFORM_TENANT_ID`, `require_platform_permission`, `roles.py`, and `StaffPermissionGrant`.
  2. `@@ -137,6 +159,134 @@ def _category_for_action(action: str) -> str:` adds `_severity_for_event` and `_affected_permissions_for_role_change`.
  3. `@@ -624,6 +783,25 @@ def list_audit_logs(` through `@@ -731,6 +916,12 @@` adds `entity_type`, `entity_id`, `request_id`, `severity`, and `affected_permissions`.
  4. `@@ -770,68 +961,134 @@ def list_platform_users(` rewrites `/users` from cross-tenant roster to platform-staff-only roster and adds department/platform/account-type filters and `allowed_actions`.
  5. `@@ -948,7 +1314,461 @@` and `@@ -992,6 +1826,561 @@` add the new lifecycle, delegated-permission, staff-serialization, profile, detail, audit, and role endpoints.
- **Key diff quotes:**

  ```diff
  +    entity_type: Optional[str] = Query(...)
  +    entity_id: Optional[str] = Query(...)
  ...
  +        data["severity"] = _severity_for_event(data["action"], data["event_metadata"])
  +        data["affected_permissions"] = (
  +            _affected_permissions_for_role_change(data["event_metadata"])
  +            if data["action"] == "OWNER_CHANGED_STAFF_ROLE"
  +            else None
  +        )
  ```

  ```diff
  -# PLATFORM-WIDE USER MANAGEMENT (cross-tenant, owner-only)
  +# SNS PLATFORM STAFF & ACCESS (SNS Hospice Solutions personnel only, owner-only)
  ...
  -        (CAST(:tenant_id AS uuid) IS NULL OR u.tenant_id = CAST(:tenant_id AS uuid))
  +        u.role = ANY(:platform_roles)
  ```

  ```diff
  +@router.patch("/users/{target_user_id}/status")
  +def set_platform_staff_status(...):
  +    ...
  +@router.post("/users/{target_user_id}/permissions", status_code=201)
  +def grant_platform_staff_permission(...):
  +    ...
  +@router.patch("/users/{target_user_id}/role", ...)
  +def update_platform_staff_role(...):
  ```

- **Merge recommendation:** do **not** take this file wholesale over current main without a manual merge. The safest plan is to preserve current-main tenant onboarding/financial/system-health code, then transplant the recovered staff-management sections as a coordinated merge with `roles.py`, `role_guards.py`, `user.py`, the migrations, and `ownerAdmin.ts`/`UserManagement.jsx`.

### `backend/app/core/account_types.py` — classified **A / NO CONFLICT**

- **Current main summary:** file absent on current `main`.
- **Recovered summary:** introduces validated account-type constants and defaulting/normalization for the four recovered staff identity types.
- **Exact changed region:** whole-file addition (`@@ -0,0 +1,42 @@`).
- **Merge recommendation:** safe to add as-is alongside migration `um2a...` and the `users.account_type` model field.

### `backend/app/core/departments.py` — classified **A / NO CONFLICT**

- **Current main summary:** file absent on current `main`.
- **Recovered summary:** introduces validated platform-department taxonomy and normalization helper, with explicit comments that department grants no permissions.
- **Exact changed region:** whole-file addition (`@@ -0,0 +1,43 @@`).
- **Merge recommendation:** safe to add as-is alongside `users.department`, the owner API response, and staff UI filters/forms.

### `backend/app/core/job_titles.py` — classified **A / NO CONFLICT**

- **Current main summary:** file absent on current `main`.
- **Recovered summary:** introduces department-scoped job-title catalogs plus validation/free-text fallback behavior for the staff profile workflow.
- **Exact changed region:** whole-file addition (`@@ -0,0 +1,84 @@`).
- **Merge recommendation:** safe to add as-is with the staff profile endpoints and UI; ensure it lands with `users.job_title` consumers already in main.

### `backend/app/models/staff_permission_grant.py` — classified **A / NO CONFLICT**

- **Current main summary:** file absent on current `main`.
- **Recovered summary:** new SQLAlchemy model for delegated platform-staff capabilities, with grant/revoke metadata and comments clarifying that the table stores grants but does not define permission semantics.
- **Exact changed region:** whole-file addition (`@@ -0,0 +1,61 @@`).
- **Merge recommendation:** safe to add as-is, but only together with migration `um2d...` and `models/__init__.py` registration.

### `backend/app/services/admin_bootstrap_service.py` — classified **B / LOW CONFLICT**

- **Current main summary:** provisions configured development identities, including a seeded OWNER account named `Development Platform Owner`.
- **Recovered summary:** same provisioning behavior, but the OWNER seed’s `full_name` changes to `SNS Tech Solutions`.
- **Exact changed region:** `@@ -40,7 +40,7 @@ DEVELOPMENT_IDENTITIES = (`.
- **Key diff quote:**

  ```diff
  -        full_name="Development Platform Owner",
  +        full_name="SNS Tech Solutions",
  ```

- **Merge recommendation:** optional safe cherry-pick; it is a branding/data choice, not a logic dependency.

### `backend/app/models/user.py` — classified **C / MEDIUM CONFLICT**

- **Current main summary:** core `User` model with tenant isolation, identity, role, HR profile basics, password-reset fields, SSN encryption helpers, and physician-linkage fields.
- **Recovered summary:** same model plus SNS Staff & Access extensions for department/notes/update tracking, account type, responsible owner/purpose/scope for non-human identities, platform assignment, and separate `platform_staff_status` lifecycle state.
- **Exact changed region:** one additive hunk at `@@ -118,6 +118,55 @@ class User(BaseModel):`.
- **Key diff quote:**

  ```diff
  +    department = Column(String(64), nullable=True)
  +    notes = Column(Text, nullable=True)
  +    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
  +    account_type = Column(String(32), nullable=False, server_default="HUMAN_STAFF")
  +    responsible_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  +    identity_purpose = Column(Text, nullable=True)
  +    identity_scope = Column(String(255), nullable=True)
  +    platform = Column(String(120), nullable=False, server_default="SNS Hospice Solutions")
  +    platform_staff_status = Column(String(32), nullable=False, server_default=text("'ACTIVE'"))
  ```

- **Merge recommendation:** merge additively with the migrations; do not omit any of the paired schema changes or the owner staff API/UI will desynchronize from the ORM.

### `backend/app/models/__init__.py` — classified **B / LOW CONFLICT**

- **Current main summary:** central model import hub used by metadata/autoload paths.
- **Recovered summary:** same file, plus import of `StaffPermissionGrant`.
- **Exact changed region:** `@@ -271,6 +271,12 @@`.
- **Key diff quote:**

  ```diff
  +from app.models.staff_permission_grant import StaffPermissionGrant
  ```

- **Merge recommendation:** take recovered hunk as-is if `staff_permission_grant.py` and migration `um2d...` are adopted.

### `sns-emr-frontend/src/owner/pages/UserManagement.jsx` — classified **D / HIGH CONFLICT**

- **Current main summary:** generic owner “User Management” page for cross-tenant users, with tenant filter, role filter, active/disabled toggle, simple stats (`total_users`, `active_now`, `agency_admins`, `disabled_users`), and password reset/enable-disable actions.
- **Recovered summary:** substantially different SNS Staff & Access page for platform personnel only, with separate Human Staff / Service Accounts / API Identities / Audit tabs, department/status filters, account-type-aware columns, backend-driven allowed actions, add/invite modal, profile drawer, and audit sub-feed.
- **Exact changed regions:**
  1. `@@ -1,26 +1,53 @@` replaces old design imports with shell icons, access-level helper, and the new modal/drawer stack.
  2. `@@ -46,11 +82,43 @@` introduces `KpiCard` and new stats shape.
  3. `@@ -58,19 +126,24 @@` and `@@ -97,15 +173,37 @@` replace tenant-filtered load state with scope/account-type/audit logic.
  4. `@@ -139,189 +237,320 @@` rewrites the rendered page layout and table entirely.
- **Key diff quotes:**

  ```diff
  -  fetchOwnerTenants,
  +  fetchOwnerAuditLogs,
  ...
  +import AddStaffModal from '../components/AddStaffModal';
  +import StaffProfileDrawer from '../components/StaffProfileDrawer';
  ```

  ```diff
  -  const [tenants, setTenants] = useState([]);
  +  const [scope, setScope] = useState('HUMAN');
  +  const [availableDepartments, setAvailableDepartments] = useState([]);
  +  const [availablePlatforms, setAvailablePlatforms] = useState(['SNS Hospice Solutions']);
  +  const [actorCapabilities, setActorCapabilities] = useState([]);
  ```

  ```diff
  -          <h1 style={S.pageTitle}>User Management</h1>
  -          <p style={S.pageSubtitle}>Orchestrate personnel access, security permissions, and roles across active agencies</p>
  +          <h1 className="text-[22px] font-bold text-text-primary">SNS Staff & Access</h1>
  +          <p className="text-sm text-text-secondary mt-1">Identity & Access Management for SNS Hospice Solutions platform personnel and platform identities</p>
  ```

- **Merge recommendation:** manual merge only, and only together with the recovered backend API and `ownerAdmin.ts`. Current-main and recovered versions solve different problems; a wholesale overwrite is risky if current-main cross-tenant user-management behavior is still needed elsewhere.

## Additional notes on other modified files

- `sns-emr-frontend/src/api/ownerAdmin.ts` should be merged with the backend `owner_admin.py` changes; it is the frontend contract for nearly every recovered staff-management feature.
- `sns-emr-frontend/src/owner/pages/AuditLogs.jsx` is another high-text-delta file (`284` additions / `155` deletions) even though it was not on the user’s explicit “must-detail” list; treat it like `UserManagement.jsx` during merge review.
- The logo asset and `BrandLogo.tsx` changes are low conflict technically, but they affect visible branding on login/owner-shell/set-password surfaces and should be reviewed with design intent in mind.
