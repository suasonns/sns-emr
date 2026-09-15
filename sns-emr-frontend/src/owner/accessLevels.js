// Shared, presentation-only Access Level labels for SNS Staff & Access.
// The actual level per role is always derived server-side
// (app.core.roles.ACCESS_LEVEL_FOR_ROLE / access_levels_by_role on the
// roster response) -- this module only turns that backend-provided code
// into a human-readable label. Never used to compute a level from a
// role locally.
export const ACCESS_LEVEL_LABELS = {
  LEVEL_1_OWNER: 'Owner',
  LEVEL_2_ADMINISTRATOR: 'Administrator',
  LEVEL_3_SPECIALIZED_ADMINISTRATOR: 'Specialized Administrator',
  LEVEL_4_OPERATIONAL_STAFF: 'Operational Staff',
  LEVEL_5_LIMITED_SUPPORT: 'Support Staff',
  LEVEL_6_READ_ONLY: 'Read Only',
};

function labelize(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

export function accessLevelLabel(level) {
  return ACCESS_LEVEL_LABELS[level] || labelize(level);
}
