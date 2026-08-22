import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));
const apiTarget =
  process.env.VITE_API_BASE_URL ??
  process.env.VITE_API_TARGET ??
  "http://localhost:8000";

// Non-production build identity badge (branch/commit). Read once at build
// time so the running app can show exactly what commit is live without
// hitting any API.
function gitInfo(cmd: string): string {
  try {
    return execSync(cmd, { cwd: frontendRoot }).toString().trim();
  } catch {
    return "unknown";
  }
}
const BUILD_BRANCH = gitInfo("git rev-parse --abbrev-ref HEAD");
const BUILD_COMMIT = gitInfo("git rev-parse --short HEAD");
// Use Vite's native import.meta.env mechanism (VITE_-prefixed process.env
// vars are picked up automatically) rather than a custom `define`, which
// proved unreliable to hot-apply in this Vite version.
process.env.VITE_BUILD_BRANCH = BUILD_BRANCH;
process.env.VITE_BUILD_COMMIT = BUILD_COMMIT;

export default defineConfig({
  root: frontendRoot,
  plugins: [react()],
  resolve: {
    preserveSymlinks: true,
  },
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
