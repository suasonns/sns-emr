// Human-readable labels for canonical backend role strings (see
// backend/app/core/roles.py). Centralized so the sidebar, staff roster,
// and any other UI surface stay consistent instead of showing raw
// SCREAMING_SNAKE_CASE role codes to end users.
const SPECIAL_LABELS = {
  DPCS_ADMINISTRATOR: 'DPCS/Administrator',
};

export function formatRoleLabel(role) {
  if (!role) return 'Staff';
  const normalized = String(role).trim().toUpperCase();
  if (SPECIAL_LABELS[normalized]) return SPECIAL_LABELS[normalized];
  return normalized
    .split('_')
    .filter(Boolean)
    .map((word) => (word.length <= 4 ? word : word.charAt(0) + word.slice(1).toLowerCase()))
    .join(' ');
}
