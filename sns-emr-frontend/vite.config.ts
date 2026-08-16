import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/auth": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/dashboard": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/visits": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/patient-charts": {
        target: "http://localhost:8000",
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
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/auth": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/dashboard": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/visits": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/patient-charts": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
