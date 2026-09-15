// Shared category metadata for the Audit Logs page and its event drawer.
// Keys must match AuditLogCategory in src/api/ownerAdmin.ts / the backend's
// VALID_AUDIT_CATEGORIES -- these are the only categories the real
// audit_logs table is ever bucketed into (derived server-side from
// `action`, see app.api.owner_admin._category_for_action).
export const CATEGORY_META = [
  { key: 'AUTH', icon: '🔐', label: 'Auth', bg: 'rgba(59,130,246,0.14)', color: '#60A5FA' },
  { key: 'DATA', icon: '📂', label: 'Data Access', bg: 'rgba(139,92,246,0.14)', color: '#A78BFA' },
  { key: 'ADMIN', icon: '⚙️', label: 'Admin', bg: 'rgba(45,212,191,0.14)', color: '#2DD4BF' },
  { key: 'BILLING', icon: '💳', label: 'Billing', bg: 'rgba(236,72,153,0.14)', color: '#EC4899' },
  { key: 'COMPLIANCE', icon: '⚠️', label: 'Compliance', bg: 'rgba(249,115,22,0.14)', color: '#FB923C' },
];

// Deterministic action -> severity classification (see
// AUDIT_SEVERITY_ACTIONS in backend/app/api/owner_admin.py -- this is a
// display-only mirror of the same static, reviewed map; the backend is
// the source of truth and returns `severity` on every log entry). Uses
// the app's official status-* Tailwind tokens 1:1 by name -- no new
// colors invented for this feature.
export const SEVERITY_META = {
  INFO: { label: 'Info', className: 'text-status-info' },
  WARNING: { label: 'Warning', className: 'text-status-warning' },
  HIGH: { label: 'High', className: 'text-status-high' },
  CRITICAL: { label: 'Critical', className: 'text-status-critical' },
};
