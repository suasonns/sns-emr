import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type ThemeMode = "dark" | "light";

type ThemeContextValue = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
};

const THEME_VARS: Record<ThemeMode, Record<string, string>> = {
  dark: {
    bg: "#0a1821",
    bgAlt: "#0d1f2a",
    card: "#101f2d",
    cardSoft: "#162b38",
    border: "#2b4256",
    teal: "#63e7d3",
    white: "#edf6ff",
    muted: "#c0d5e5",
    dim: "#7f9bb1",
    green: "#4ec98d",
    blue: "#7ab6ff",
    purple: "#8e7ae6",
    orange: "#f7bb5c",
    red: "#f56b6b",
    yellow: "#f4d06a",
    pink: "#ee7cc1",
    shadow: "rgba(2, 6, 23, 0.46)",
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
