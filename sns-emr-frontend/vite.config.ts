import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget =
  process.env.VITE_API_BASE_URL ??
  process.env.VITE_API_TARGET ??
  "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/auth": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/dashboard": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/audit-dashboard": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/visits": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/patient-charts": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
    host: true,
    allowedHosts: true,
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/auth": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/dashboard": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/audit-dashboard": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/visits": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/patient-charts": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }

          if (
            id.includes("react") ||
            id.includes("react-dom") ||
            id.includes("scheduler") ||
            id.includes("react-router")
          ) {
            return "react-vendor";
          }

          if (id.includes("@mui") || id.includes("@emotion")) {
            return "mui-vendor";
          }

          if (id.includes("axios")) {
            return "axios-vendor";
          }

          return "vendor";
        },
      },
    },
  },
});
