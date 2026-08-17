// Shared color palette for patient chart / intake board components.
// Ensures every board screen (Facesheet, Consent & Notifications, Staff
// Assignment, Chart Completion Checklist, etc.) switches cleanly between
// dark and light mode using the same tokens.
export const getChartColors = (mode) => mode === 'light' ? {
  bg: '#f3f8f7',
  card: '#ffffff',
  border: '#d9e6eb',
  teal: '#0d7d7a',
  white: '#18354c',
  label: '#5f7286',
  text: '#1e2d3b',
  green: '#2d7b63',
  red: '#d64d57',
  amber: '#d38a2b',
  greenBg: '#dff5ee',
  redBg: '#fbe3e7',
  amberBg: '#f9edd7',
  tealBg: '#dff8f4',
} : {
  bg: '#0f172a',
  card: '#1e293b',
  border: '#334155',
  teal: '#10b7a2',
  white: '#ffffff',
  label: '#94a3b8',
  text: '#e2e8f0',
  green: '#059669',
  red: '#ef4444',
  amber: '#f59e0b',
  greenBg: '#05966915',
  redBg: '#ef444415',
  amberBg: '#f59e0b15',
  tealBg: '#10b7a215',
};

export default getChartColors;
