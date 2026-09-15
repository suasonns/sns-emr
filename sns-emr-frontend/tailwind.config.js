/** @type {import('tailwindcss').Config} */
module.exports = {
  // Scoped to avoid Tailwind's Preflight base reset clashing with the
  // existing MUI/CssBaseline + inline-style pages used elsewhere in the app.
  // Only classes actually used inside src/** are generated; Preflight is
  // disabled below so unrelated pages keep their current appearance.
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  corePlugins: {
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        // All values below resolve through CSS custom properties defined in
        // src/owner/shell/tailwind.css, which switch between the dark and
        // light Figma palettes based on the existing `data-theme` attribute
        // (see applyThemeMode() in src/theme/theme.tsx). Colors that are used
        // with Tailwind opacity modifiers elsewhere (e.g. `bg-ai/10`) use the
        // `rgb(var(...) / <alpha-value>)` pattern so opacity keeps working.
        sns: {
          app: 'var(--owner-app)',
          main: 'var(--owner-main)',
          card: 'var(--owner-card)',
          elevated: 'var(--owner-elevated)',
          'card-alt': 'var(--owner-elevated)',
          sidebar: 'var(--owner-sidebar)',
          topbar: 'var(--owner-topbar)',
          row: 'var(--owner-row)',
          column: 'var(--owner-column)',
          pulse: 'var(--owner-pulse)',
          border: 'var(--owner-border)',
          'border-subtle': 'var(--owner-border-subtle)',
          'border-active': 'var(--owner-border-active)',
          'pill-border': 'var(--owner-pill-border)',
        },
        ai: {
          DEFAULT: 'rgb(var(--owner-ai-rgb) / <alpha-value>)',
          bg: 'rgb(var(--owner-ai-bg-rgb) / <alpha-value>)',
          'gradient-start': 'var(--owner-ai-gradient-start)',
          'badge-bg': 'var(--owner-ai-badge-bg)',
          'badge-border': 'var(--owner-ai-badge-border)',
          // Readable text/icon color for solid bg-ai buttons; the AI accent
          // is bright teal in dark mode (needs dark text) and deep teal in
          // light mode (needs white text), so it can't be a fixed literal.
          on: 'var(--owner-ai-on)',
        },
        text: {
          primary: 'var(--owner-text-primary)',
          body: 'var(--owner-text-body)',
          secondary: 'var(--owner-text-secondary)',
          tertiary: 'var(--owner-text-tertiary)',
        },
        status: {
          healthy: 'rgb(var(--owner-status-healthy-rgb) / <alpha-value>)',
          high: 'rgb(var(--owner-status-high-rgb) / <alpha-value>)',
          warning: 'rgb(var(--owner-status-warning-rgb) / <alpha-value>)',
          critical: 'rgb(var(--owner-status-critical-rgb) / <alpha-value>)',
          monitor: 'rgb(var(--owner-status-monitor-rgb) / <alpha-value>)',
          info: 'rgb(var(--owner-status-info-rgb) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        panel: '0 8px 24px -8px rgba(0, 0, 0, 0.15)',
        'ai-panel': '0 0 24px 8px rgba(45, 212, 191, 0.07), 0 8px 24px -8px rgba(0, 0, 0, 0.15)',
        'critical-glow': '0 0 28px 12px rgba(244, 63, 94, 0.12)',
        'high-glow': '0 0 20px 10px rgba(56, 189, 248, 0.08)',
        'ai-btn': '0 2px 8px rgba(45, 212, 191, 0.08)',
        topbar: '0 4px 12px -6px rgba(0, 0, 0, 0.15)',
      },
    },
  },
  plugins: [],
};
