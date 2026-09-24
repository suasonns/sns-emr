import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type ThemeMode = "dark" | "light";

type ThemeContextValue = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
};

const THEME_VARS: Record<ThemeMode, Record<string, string>> = {
  dark: {
    // [LIVELY CLINICAL SLATE -- 2026-09-22] Final approved dark-theme
    // token set per SNS_LIVELY_DARK_THEME directive. Semantic token names
    // are preserved/extended (no parallel theme system): existing
    // consumers of bg/bgAlt/card/cardSoft/border/teal/white/muted/dim/
    // green/blue/purple/orange/red/yellow/pink/shadow keep working
    // unchanged; new keys below are additive for hover/selected/focus/
    // status-background/border-variant states used by the RNICA rail,
    // buttons, and form controls. Light theme (below) is untouched for
    // every pre-existing key; new keys get light-appropriate values so
    // components can share the same var() names in both modes.
    bg: "#07111d",
    bgAlt: "#091525",
    card: "#101f31",
    cardSoft: "#182c42",
    border: "rgba(148, 163, 184, 0.16)",
    teal: "#35e0c1",
    white: "#f8fafc",
    muted: "#a9bcd0",
    dim: "#7890a8",
    green: "#4ade80",
    blue: "#38bdf8",
    purple: "#a78bfa",
    orange: "#fbbf24",
    red: "#fb7185",
    yellow: "#f4d06a",
    pink: "#ee7cc1",
    shadow: "rgba(0, 0, 0, 0.22)",
    shadowStrong: "rgba(0, 0, 0, 0.28)",

    // Additional surfaces
    bgDeep: "#091525",
    bgNav: "#0c1a2b",
    workspaceBg: "#0a1624",
    inputBg: "#0d1b2b",
    hoverSurface: "#1c334b",
    selectedSurface: "#163a48",

    // Text tiers beyond white/muted/dim
    textStrong: "#dce7f3",
    textDisabled: "#526a82",
    textInverse: "#031317",

    // Teal state variants + secondary accent
    tealHover: "#5ce9d0",
    tealPressed: "#20bfa4",
    tealSoftBg: "rgba(53, 224, 193, 0.12)",
    tealSoftBorder: "rgba(53, 224, 193, 0.34)",
    cyan: "#46cff1",

    // Status backgrounds (paired with existing green/blue/orange/red/purple
    // as the status foreground colors)
    successBg: "rgba(74, 222, 128, 0.12)",
    infoBg: "rgba(56, 189, 248, 0.12)",
    warningBg: "rgba(251, 191, 36, 0.12)",
    criticalBg: "rgba(251, 113, 133, 0.12)",
    aiBg: "rgba(167, 139, 250, 0.12)",

    // Border variants
    borderStrong: "rgba(148, 163, 184, 0.28)",
    borderSelected: "rgba(53, 224, 193, 0.50)",
    borderWarning: "rgba(251, 191, 36, 0.48)",
    borderCritical: "rgba(251, 113, 133, 0.48)",
    borderAI: "rgba(167, 139, 250, 0.44)",

    // Focus
    focusRing: "#5eead4",
    focusHalo: "rgba(94, 234, 212, 0.28)",

    // Scrim / elevated shadows
    overlay: "rgba(2, 8, 23, 0.72)",
    shadowDrawer: "rgba(0, 0, 0, 0.48)",
  },
  light: {
    bg: "#f3f8f7",
    bgAlt: "#edf5f3",
    card: "#ffffff",
    cardSoft: "#f3f7fa",
    border: "#d9e6eb",
    teal: "#0d7d7a",
    white: "#18354c",
    muted: "#4a5f73",
    dim: "#6d7d8b",
    green: "#2d7b63",
    blue: "#4d7dc2",
    purple: "#7b61d8",
    orange: "#d38a2b",
    red: "#d64d57",
    yellow: "#b7861b",
    pink: "#cf5eb7",
    shadow: "rgba(15, 23, 42, 0.08)",
    shadowStrong: "rgba(15, 23, 42, 0.16)",

    // Additional surfaces (light-mode equivalents of the new dark tokens
    // above; these preserve the existing light appearance since nothing
    // consumed these names before this change)
    bgDeep: "#e7f1ef",
    bgNav: "#e9f2f0",
    workspaceBg: "#eef6f4",
    inputBg: "#ffffff",
    hoverSurface: "#e4f1ee",
    selectedSurface: "#dcf3ee",

    textStrong: "#1f2937",
    textDisabled: "#94a3b8",
    textInverse: "#ffffff",

    tealHover: "#0a6663",
    tealPressed: "#095350",
    tealSoftBg: "rgba(13, 125, 122, 0.10)",
    tealSoftBorder: "rgba(13, 125, 122, 0.28)",
    cyan: "#1d8fae",

    successBg: "rgba(45, 123, 99, 0.10)",
    infoBg: "rgba(77, 125, 194, 0.10)",
    warningBg: "rgba(211, 138, 43, 0.10)",
    criticalBg: "rgba(214, 77, 87, 0.10)",
    aiBg: "rgba(123, 97, 216, 0.10)",

    borderStrong: "#c3d6dc",
    borderSelected: "rgba(13, 125, 122, 0.45)",
    borderWarning: "rgba(211, 138, 43, 0.4)",
    borderCritical: "rgba(214, 77, 87, 0.4)",
    borderAI: "rgba(123, 97, 216, 0.4)",

    focusRing: "#0d7d7a",
    focusHalo: "rgba(13, 125, 122, 0.22)",

    overlay: "rgba(15, 23, 42, 0.45)",
    shadowDrawer: "rgba(15, 23, 42, 0.24)",
  },
};

const STORAGE_KEY = "sns-hospice-theme-mode";

function getStoredMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  const saved = window.localStorage.getItem(STORAGE_KEY);
  return saved === "light" || saved === "dark" ? saved : "dark";
}

export function applyThemeMode(mode: ThemeMode) {
  const root = document.documentElement;
  const variables = THEME_VARS[mode];

  Object.entries(variables).forEach(([key, value]) => {
    root.style.setProperty(`--sns-${key}`, value);
  });

  root.dataset.theme = mode;
  document.body.style.background = variables.bg;
  document.body.style.color = variables.white;
  window.localStorage.setItem(STORAGE_KEY, mode);
}

const ThemeModeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => getStoredMode());

  useEffect(() => {
    applyThemeMode(mode);
  }, [mode]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      mode,
      setMode: (nextMode) => setModeState(nextMode),
      toggleMode: () => setModeState((current) => (current === "dark" ? "light" : "dark")),
    }),
    [mode]
  );

  return <ThemeModeContext.Provider value={value}>{children}</ThemeModeContext.Provider>;
}

export function useThemeMode() {
  const context = useContext(ThemeModeContext);

  if (!context) {
    throw new Error("useThemeMode must be used within ThemeModeProvider");
  }

  return context;
}
