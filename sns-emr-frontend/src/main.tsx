import React from "react";
import ReactDOM from "react-dom/client";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import App from "./App";
import { ThemeModeProvider } from "./theme/theme";
import { registerSW } from "virtual:pwa-register";

// Registers the production service worker so the app shell (not any
// patient data) can load with zero connectivity. A no-op in dev, where
// devOptions.enabled is false (see vite.config.ts).
registerSW({ immediate: true });

const theme = createTheme({
  typography: {
    fontFamily: 'Inter, "Segoe UI", Roboto, sans-serif',
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeModeProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </ThemeModeProvider>
  </React.StrictMode>,
);
