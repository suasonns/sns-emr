import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type ThemeMode = "dark" | "light";

type ThemeContextValue = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
};

const THEME_VARS: Record<ThemeMode, Record<string, string>> = {
  dark: {
    // [VISUAL POLISH -- 2026-09-22] Modernized dark palette: less neon/
    // saturated teal, clearer surface-elevation steps (bg < bgAlt < card <
    // cardSoft), lower-contrast borders, deeper card shadows. Presentation
    // only -- no RNICA field, validation, or behavior is affected by these
    // token values.
    bg: "#0a1119",
    bgAlt: "#0e1922",
    card: "#131f2b",
    cardSoft: "#1a2938",
    border: "#1e2b38",
    teal: "#4fb8ac",
    white: "#e7edf3",
    muted: "#a6bacb",
    dim: "#71889b",
    green: "#4ec98d",
    blue: "#6fa2d6",
    purple: "#8e7ae6",
    orange: "#f7bb5c",
    red: "#f56b6b",
    yellow: "#f4d06a",
    pink: "#ee7cc1",
    shadow: "rgba(2, 6, 23, 0.55)",
    shadowStrong: "rgba(1, 4, 10, 0.7)",
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
