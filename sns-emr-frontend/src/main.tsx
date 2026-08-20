import React from "react";
import ReactDOM from "react-dom/client";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import App from "./App";
import { ThemeModeProvider } from "./theme/theme";

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
