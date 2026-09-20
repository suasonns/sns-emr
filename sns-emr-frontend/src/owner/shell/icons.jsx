import React from 'react';

/**
 * Icon set for the Owner Platform's icon-only sidebar (SNS Operations
 * Command Center redesign). One distinct glyph per real nav item —
 * intentionally simple, single-stroke-weight outlines so the set reads
 * as one consistent family rather than a mix of icon libraries.
 */
const baseProps = {
  width: 20,
  height: 20,
  viewBox: '0 0 20 20',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export const IconDashboard = () => (
  <svg {...baseProps}>
    <rect x="2.5" y="2.5" width="6.5" height="6.5" rx="1.3" />
    <rect x="11" y="2.5" width="6.5" height="6.5" rx="1.3" />
    <rect x="2.5" y="11" width="6.5" height="6.5" rx="1.3" />
    <rect x="11" y="11" width="6.5" height="6.5" rx="1.3" />
  </svg>
);

export const IconBuilding = () => (
  <svg {...baseProps}>
    <rect x="4" y="2.5" width="9" height="15" rx="1" />
    <path d="M13 8h3v9.5h-3M7 5.5h.01M10.3 5.5h.01M7 8.5h.01M10.3 8.5h.01M7 11.5h.01M10.3 11.5h.01" />
  </svg>
);

export const IconHeartPulse = () => (
  <svg {...baseProps}>
    <path d="M17 8.6c0-2.3-1.9-4.1-4.1-4.1-1.2 0-2.3.5-3 1.4a3.9 3.9 0 00-3-1.4C4.7 4.5 3 6.3 3 8.6c0 4.4 6.9 8.4 6.9 8.4S17 13 17 8.6z" />
    <path d="M4.5 9.5h2l1-2 1.8 4 1.2-2h4.7" />
  </svg>
);

export const IconUsers = () => (
  <svg {...baseProps}>
    <circle cx="7" cy="6.5" r="2.5" />
    <path d="M2.5 17c0-2.8 2-5 4.5-5s4.5 2.2 4.5 5" />
    <circle cx="14.5" cy="7" r="2" />
    <path d="M13.5 12.3c2.2.3 3.9 2.3 3.9 4.7" />
  </svg>
);

export const IconClipboard = () => (
  <svg {...baseProps}>
    <rect x="4" y="3.5" width="12" height="14" rx="1.5" />
    <rect x="7" y="2" width="6" height="3" rx="1" />
    <path d="M7 9h6M7 12h6M7 15h3.5" />
  </svg>
);

export const IconTrendChart = () => (
  <svg {...baseProps}>
    <path d="M3 16.5V3.5M3 16.5h14" />
    <path d="M5.5 13l3-3.5 2.5 2 4.5-6" />
  </svg>
);

export const IconCreditCard = () => (
  <svg {...baseProps}>
    <rect x="2.5" y="4.5" width="15" height="11" rx="1.5" />
    <path d="M2.5 8h15M5.5 12.5h3" />
  </svg>
);

export const IconSettingsGear = () => (
  <svg {...baseProps}>
    <circle cx="10" cy="10" r="2.6" />
    <path d="M10 3v1.6M10 15.4V17M17 10h-1.6M4.6 10H3M14.8 5.2l-1.1 1.1M6.3 13.7l-1.1 1.1M14.8 14.8l-1.1-1.1M6.3 6.3L5.2 5.2" />
  </svg>
);

export const IconSparkles = ({ className = '' }) => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor"
    strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9 1v3M9 14v3M1 9h3M14 9h3M3.5 3.5l2 2M12.5 12.5l2 2M14.5 3.5l-2 2M5.5 12.5l-2 2" />
  </svg>
);

export const IconStethoscope = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#fff" strokeWidth="1.5"
    strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 3v5a5 5 0 0010 0V3" />
    <circle cx="15" cy="14" r="2" />
    <path d="M15 16v1a3 3 0 01-3 3h-1a3 3 0 01-3-3v-1" />
  </svg>
);

export const IconBell = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5"
    strokeLinecap="round">
    <path d="M13.5 6.75a4.5 4.5 0 10-9 0c0 5.25-2.25 6.75-2.25 6.75h13.5s-2.25-1.5-2.25-6.75" />
    <path d="M10.3 15.75a1.5 1.5 0 01-2.6 0" />
  </svg>
);

export const IconSunMoon = ({ mode }) =>
  mode === 'dark' ? (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15.5 10.4A6.5 6.5 0 017.6 2.5a6.5 6.5 0 107.9 7.9z" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="9" cy="9" r="3.2" />
      <path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.6 3.6l1.4 1.4M13 13l1.4 1.4M14.4 3.6L13 5M5 13l-1.4 1.4" />
    </svg>
  );

export const IconChevronDown = ({ className = '' }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
    strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M4 6l4 4 4-4" />
  </svg>
);

export const IconCalendar = ({ className = '' }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
    strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="3.5" width="12" height="10.5" rx="1.5" />
    <path d="M2 6.5h12M5.5 2v3M10.5 2v3" />
  </svg>
);

export const IconPlus = ({ className = '' }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
    strokeLinecap="round" className={className}>
    <path d="M8 3v10M3 8h10" />
  </svg>
);

export const IconCheck = ({ className = '' }) => (
  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M2 5l2 2 4-4" />
  </svg>
);

export const IconClose = ({ className = '' }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
    strokeLinecap="round" className={className}>
    <path d="M3 3l10 10M13 3L3 13" />
  </svg>
);

export const IconLogout = () => (
  <svg width="16" height="16" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M7 15.5H4a1.5 1.5 0 01-1.5-1.5V4A1.5 1.5 0 014 2.5h3" />
    <path d="M12 12.5L16 9l-4-3.5M16 9H7" />
  </svg>
);

/** Maps each real Owner Platform nav key to its icon component. */
export const NAV_ICONS = {
  dashboard: IconDashboard,
  tenants: IconBuilding,
  health: IconHeartPulse,
  users: IconUsers,
  audit: IconClipboard,
  analytics: IconTrendChart,
  billing: IconCreditCard,
  settings: IconSettingsGear,
  ai: IconSparkles,
};
