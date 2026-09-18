# COMMUNICATIONS DISCOVERY REPORT

STATUS: DISCOVERY COMPLETE — NO DESIGN OR IMPLEMENTATION AUTHORIZED

This report is a repository-verified inventory of everything already
built in this codebase that relates to a "Communications Module"
(messaging, notifications, conversations, channels, realtime,
attachments). It does not propose an architecture. It exists so that
a future Communications Module spec is written against reality, not
against assumptions.

Every claim below is backed by an exact file path. Where a claim could
not be verified in the repository, it is explicitly marked as NOT
FOUND rather than guessed.

---

## 1. EXECUTIVE SUMMARY

- There is **no person-to-person messaging/chat system** anywhere in
  this codebase. No `Message`, `Conversation`, `Thread`, or `Channel`
  model exists in the backend. This is confirmed both by repository
  search and by an explicit in-code comment on the currently-routed
  frontend page (see Section 4.1).
- There **is** a working, tenant-scoped, patient-scoped **in-app
  notification system** (`Notification` model + CRUD API), currently
  used only as a side-effect of two features (task due-date reminders
  and Communications Log alerts), with **zero frontend consumer**.
- There **is** a working, tenant-scoped **Communications Log**
  (`CommunicationsLog` model + full lifecycle API) for logging clinical
  contact events (phone calls, on-call notes, family concerns, etc.)
  per patient. This is a clinical **event log**, not a messaging
  system — there is no send/reply/thread concept.
- There is **no websocket or realtime infrastructure** in application
  code. A `websockets` package appears in `requirements.lock.txt` only
  as a transitive dependency of `uvicorn[standard]`; it is not
  imported or used anywhere under `backend/app`.
- There are **two conflicting "Secure Inbox" frontend implementations**
  — one is an honest "not built yet" placeholder that is the one
  actually routed at `/secure-inbox`, `/messaging`, and `/messenger`;
  the other is a fully hardcoded fake-message mock reachable through a
  separate, older tenant-portal shell (`/tenant`, `/portal`). This is
  flagged as a live inconsistency, not a recommendation to build
  either into a real system.

---

## 2. BACKEND — DATA MODELS

### 2.1 `Notification` (REUSE candidate)
**File:** `backend/app/models/notification.py`
**Table:** `notifications` (created in Alembic baseline migration
`backend/alembic/versions/521d501c6eea_consolidated_baseline.py`)

Fields: `id`, `tenant_id`, `user_id`, `patient_id` (nullable),
`title`, `message`, `notification_type`, `source_type`, `source_id`,
`is_read`, `read_at`, `created_at`.

This is a generic, tenant-scoped, per-user, source-traceable
notification record. It is **not** a message between two users — it
has no `sender_id`/`recipient_id` pair, no reply/thread concept, and
no delivery channel (SMS/email/push) fields. It is a flat "system told
user X about event Y" record.

Classification: **REUSE** — this is a solid foundation for an in-app
notification/alert feed. It is not itself a messaging system and
should not be conflated with one.

### 2.2 `CommunicationsLog` (REUSE candidate, not a messaging model)
**File:** `backend/app/models/communications_log.py`
**Table:** `communications_logs`

Fields: `id`, `tenant_id`, `patient_id`, `event_type`, `focus_area`,
`event_time`, `summary`, `details` (JSON), `created_by`, `created_at`,
plus a lifecycle: `status` (default `RECEIVED`), `acknowledged_by`/
`acknowledged_at`, `verified_by`/`verified_at`, `resolved_by`/
`resolved_at`.

This is a **clinical contact/event log** per patient (phone calls,
on-call notes, family concerns, reminders) with an acknowledge →
verify → resolve workflow. It has no concept of a conversation
between two specific people, no recipient list, and no "reply."
Downstream, a `CommunicationsLog` entry can trigger:
- an in-app `Notification` via `create_commlog_alerts` (Section 3.2),
- a task via `handle_commlog_for_tasks` (`backend/app/services/commlog_to_task_bridge.py`),
- an IDG intelligence item via `create_or_update_from_communication_log`
  (`backend/app/services/idg_intelligence_service.py`),
- a "family concern" record via
  `create_or_update_family_concern_from_source`
  (`backend/app/services/hospitalization_prevention_service.py`),
- an evidence-harvest entry via `harvest_from_source`
  (`backend/app/services/evidence/harvest_service.py`).

Classification: **REUSE** for its stated purpose (clinical event
logging feeding IDG/tasks/notifications). **NOT REUSABLE** as a
messaging backbone — it was not designed for two-way, threaded,
user-to-user communication.

### 2.3 `DocumentNotification` (REUSE candidate, narrow scope)
**File:** `backend/app/models/document_notification.py`
**Table:** `document_notifications`

Fields: `id`, `document_id` (FK to `document_records`),
`recipient_role`, `recipient_user_id` (nullable FK to `users`),
`notified_at`, `acknowledged_at`, `reminder_count`,
`last_reminder_at`, plus resolution fields (`resolution_status`,
`resolution_note`, `resolved_at`, `resolved_by`). Comment in file notes
resolution fields were "added via Alembic migration" as a follow-up.

This is a narrow, document-specific notify/acknowledge/resolve record
— conceptually a sibling of `Notification`, scoped only to documents
requiring review. Classification: **REUSE** for document-review
notification flows specifically; not a general messaging model.

### 2.4 No `Message` / `Conversation` / `Thread` / `Channel` models exist
Verified by direct class-name search across `backend/app` — no matches
for `class Conversation`, `class Channel`, `class Message`,
`class Thread`, `class ChatRoom`, or `class DirectMessage`. There is
also no message/thread table in the Alembic baseline migration.
Classification: **NOT FOUND** — nothing to reuse or extend here; any
real messaging feature starts from zero on the data-model side.

### 2.5 No message-specific attachment support exists
No attachment table or field tied to a message/conversation was found
(none exists to be tied to, per 2.4). General document/file-upload
infrastructure exists elsewhere in the platform (e.g.
`document_records`, `document_notifications`) but is not
message-scoped. Classification: **NOT FOUND** for message attachments
specifically.

---

## 3. BACKEND — SERVICES AND API ROUTES

### 3.1 Notification API — `backend/app/api/notifications.py`
Registered in `backend/app/api/registry.py`
(`from app.api.notifications import router as notifications_router`),
so it is live and reachable.

Routes (prefix implied by router, all under `/notifications`):
- `GET /notifications?user_id=` — list a user's notifications, newest
  first.
- `GET /notifications/unread-count?user_id=` — unread count.
- `PATCH /notifications/{notification_id}/read` — mark one read.
- `PATCH /notifications/read-all?user_id=` — mark all read for a user.

Assessment: **fully functional CRUD surface**, but thin —
`user_id` is passed as a query parameter rather than derived from the
authenticated session/current user in every endpoint, and there is no
tenant-scoping filter applied in the queries shown (queries filter by
`user_id` only, not by `tenant_id`). No frontend caller was found for
any of these four routes (see Section 4.2). Classification:
**EXTEND** if kept as the notification backbone — needs auth-derived
user identity, explicit tenant scoping, and a frontend consumer before
it is production-safe as-is.

### 3.2 Notification creation service — `backend/app/services/notification_engine.py`
`create_notification(...)` — the single writer used to create
`Notification` rows. Defensive (`if not user_id or not tenant_id:
return`). Called from:
- `backend/app/services/communications_log_alerts.py` —
  `create_commlog_alerts(...)`, fires one notification per
  patient-assigned/clinical-admin recipient when a Communications Log
  entry is created. Comment states privacy rule: "never broadcast
  globally."
- `backend/app/services/task_notification_engine.py` —
  `run_task_notification_engine(...)`, a pre-due-date reminder engine
  for `POC_UPDATE` tasks (3 days before, 1 day before, due today).
  **Its actual notification delivery is a stub**: the `_notify()`
  function only does `print(...)` to console — it does not call
  `create_notification` and does not persist anything. Classification:
  **INCOMPLETE** — this engine does not currently produce any
  `Notification` row despite being named a notification engine.

### 3.3 Document notification service — `backend/app/services/document_notifications.py`
`create_document_notifications(...)` — resolves patient-assigned
recipients via `resolve_patient_recipients` and creates one
`DocumentNotification` row per recipient plus an audit event. This is
a working, narrow pipeline for document-review notifications, separate
from the generic `Notification` model. Classification: **REUSE** for
its scope; note it is a second, parallel notification concept
(`DocumentNotification` vs. `Notification`) rather than a variant of
the first — any Communications Module discovery must not assume these
two converge automatically.

### 3.4 Communications Log API — `backend/app/api/communications_log/router.py`
Prefix: `/communications-log`. Routes found:
- `POST /communications-log` — create a log entry (blocked for
  OWNER/BILLING roles via `require_create_access`).
- `GET /communications-log/patients/` — list entries.
- `POST /communications-log/{commlog_id}/acknowledge`
- `POST /communications-log/{commlog_id}/verify`
- `POST /communications-log/{commlog_id}/resolve`

On create, the router fans out to alerting (3.2), task bridging, IDG
intelligence, family-concern detection, and evidence harvesting (see
Section 2.2). This is a mature, multi-consumer, tenant-schema-aware
(`_resolve_tenant_schema_name` / `_apply_tenant_search_path`)
subsystem. Classification: **REUSE** — functionally complete for
clinical contact logging; not a messaging system and should not be
repurposed as one without a distinct data model.

### 3.5 No websocket / realtime endpoints exist
No `WebSocket` usage, socket.io, Pusher, Ably, SignalR, or pub/sub
pattern was found anywhere under `backend/app`. The only hit for
"websocket" in the whole backend tree is the `websockets==16.0` line
in `requirements.lock.txt`, which is a transitive dependency pulled in
by `uvicorn` (used for its own optional HTTP/1.1 upgrade support), not
something the application imports or uses. Classification:
**NOT FOUND** — there is no realtime transport layer to reuse; a live
chat feature would need one built or added from scratch.

---

## 4. FRONTEND — ROUTES AND COMPONENTS

### 4.1 The currently-routed "Secure Inbox" / "Messaging" pages are honest placeholders
**File:** `sns-emr-frontend/src/pages/SecureInboxDataPage.tsx`
**Routed at (in `App.tsx`):** `/secure-inbox`, `/messaging`,
`/messenger` — all three routes render this same component.

The file contains this exact in-code comment, which is itself
authoritative discovery evidence:

> "This page previously rendered getDemoInbox() -- 6 fully fabricated
> message threads (fake senders, fake patient names, fake unread
> counts) with no backend behind any of it. There is no
> secure-messaging/message-center model, API, or data store anywhere
> in this codebase. Per the project's standing 'never fabricate data'
> policy (same rule behind billing's ComingSoonPage), this now shows
> an honest not-yet-available state instead of sample threads."

The rendered UI is a single "Secure messaging not available yet" empty
state — no list, no compose, no fetch call. Classification:
**INCOMPLETE (intentionally, by policy)** — this is the correct
current behavior per the project's no-fabrication rule, not a bug.

### 4.2 A conflicting, fully-mocked "Secure Inbox" also exists and is still reachable
**File:** `sns-emr-frontend/src/tenant/pages/SecureInbox.jsx`
Hardcoded array `MESSAGES` with 4 fake entries ("MD Office", "Family
Member", "Clinical Team", "Billing"), a fake folder list with a
hardcoded unread count of `12`, and a non-functional "Compose Message"
button. No API call of any kind.

This component is imported and rendered by
`sns-emr-frontend/src/tenant/TenantDashboard.jsx` (`pages.push(SecureInbox,
Settings)`, imported via `sns-emr-frontend/src/tenant/pages/index.js`),
and `TenantDashboard` is itself live-routed in `App.tsx` at `/tenant`
and `/portal`.

**This is a direct contradiction of the policy documented in 4.1**:
one route family shows an honest empty state, another live route shows
fabricated message threads with a fake unread badge. Classification:
**DEPRECATED / INCONSISTENT** — flagged as a defect to resolve
(remove or replace this mock) independent of any future Communications
Module build, not something to extend.

### 4.3 `CommunicationLogPage.tsx` — patient-scoped clinical log UI, currently mocked
**File:** `sns-emr-frontend/src/pages/CommunicationLogPage.tsx`
Rendered inside `PatientModuleShell` as one of a patient chart's
section tabs ("Communication Log"). Fetches the patient's name via
`fetchPatientSummary`, but the log itself — `logEntries`, `logTypes`,
`metrics`, `patientOverview` — is all hardcoded sample data. It does
**not** call the working `communications-log` API described in Section
3.4. Classification: **INCOMPLETE** — the backend it should be wired
to already exists; this page has simply not been connected to it yet.

### 4.4 Notification API has no frontend consumer at all
No file under `sns-emr-frontend/src` calls `/notifications`,
`/notifications/unread-count`, or any notification-read endpoint.
Search of `sns-emr-frontend/src/api` for "notification" only turns up
unrelated boolean fields on visit/assessment payloads (e.g.
`rn_notification_required`) — not calls to the notification API.
`MyProfilePage.tsx` has an "SMS Urgent Alerts" toggle, but it is a
local UI toggle with no evidence of being wired to any notification
preference storage or delivery mechanism. Classification: **NOT FOUND**
— no notification bell, feed, or toast UI exists; the working backend
API from Section 3.1 is entirely orphaned today.

---

## 5. CLASSIFICATION SUMMARY

| Component | Type | File(s) | Classification |
|---|---|---|---|
| `Notification` model + CRUD API | Backend | `models/notification.py`, `api/notifications.py`, `services/notification_engine.py` | REUSE (needs auth-derived user + tenant scoping fixes) |
| Task pre-due notification engine | Backend | `services/task_notification_engine.py` | INCOMPLETE (delivery is a `print()` stub, not persisted) |
| `DocumentNotification` model + service | Backend | `models/document_notification.py`, `services/document_notifications.py` | REUSE (narrow, document-review scope only) |
| `CommunicationsLog` model + API | Backend | `models/communications_log.py`, `api/communications_log/router.py` | REUSE (clinical event log; not a messaging model) |
| `Message`/`Conversation`/`Thread`/`Channel` models | Backend | — | NOT FOUND |
| Websocket / realtime transport | Backend | — | NOT FOUND (transitive dep only, unused) |
| Message-specific attachments | Backend | — | NOT FOUND |
| `/secure-inbox`, `/messaging`, `/messenger` routes | Frontend | `pages/SecureInboxDataPage.tsx`, `App.tsx` | INCOMPLETE (honest placeholder, by policy) |
| `tenant/pages/SecureInbox.jsx` via `/tenant`, `/portal` | Frontend | `tenant/pages/SecureInbox.jsx`, `tenant/TenantDashboard.jsx` | DEPRECATED (fabricated data, contradicts stated policy) |
| `CommunicationLogPage.tsx` (patient chart tab) | Frontend | `pages/CommunicationLogPage.tsx` | INCOMPLETE (not wired to real communications-log API) |
| Notification bell/feed UI | Frontend | — | NOT FOUND |

---

## 6. OPEN QUESTIONS FOR BEFORE ANY DESIGN WORK

1. Should a future Communications Module be built as a genuinely new
   `Message`/`Conversation` subsystem, or should "Communications" for
   this platform continue to mean the existing `CommunicationsLog`
   (clinical event log) plus `Notification` (in-app alert feed)
   pattern, extended rather than replaced?
2. Is `tenant/pages/SecureInbox.jsx` (the fabricated-data version,
   Section 4.2) intended to be deleted now as a policy violation, or
   is it in scope for the Communications Module discovery to resolve?
3. Should `DocumentNotification` and `Notification` be unified, or are
   they intentionally meant to stay separate parallel systems?
4. Is realtime delivery (websockets) actually a requirement, or is a
   polling/refresh-based notification feed acceptable for v1?

No answers to these questions are assumed or implied by this report.

---

## 7. RELATIONSHIP TO OTHER DOCUMENTS

This report is scoped only to Communications/messaging discovery. It
is independent of, and does not modify,
`docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` (Biller
Platform entity discovery) or
`docs/room-board/ROOM_BOARD_IMPLEMENTATION_PLAN_SCHEMA_AND_ISSUES.md`
(Room & Board engineering plan). No schema, migration, model, or route
changes were made while producing this report.

---

## 8. CHANGE LOG

| Date | Change |
|---|---|
| 2026-09-17 | Document created. Full repository discovery of messaging/notification/communications infrastructure completed per explicit instruction: do not design or build, discovery only. Findings: no Message/Conversation/Thread/Channel model or websocket/realtime infrastructure exists (NOT FOUND); a working Notification model/API exists but has no frontend consumer (REUSE, orphaned); a working CommunicationsLog clinical event-log model/API exists with multiple downstream consumers (REUSE, not a messaging system); a task pre-due notification engine exists but its delivery step is an unpersisted console-print stub (INCOMPLETE); the live-routed Secure Inbox/Messaging pages correctly show an honest "not built" placeholder (INCOMPLETE by policy) while a separate, still-reachable tenant-portal Secure Inbox page shows fully fabricated message data (DEPRECATED, flagged as a policy-violating inconsistency); the patient-chart Communication Log tab is UI-only and not wired to the real backend API (INCOMPLETE). Documentation only; no schema, migrations, tables, models, or routes created or changed. |
