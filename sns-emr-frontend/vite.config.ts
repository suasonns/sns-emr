import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

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

// Single source of truth for every backend API path prefix the frontend
// calls (see backend/app/api/registry.py for the full router list). Both
// the dev server and preview proxy are built from this list so a prefix
// added here never silently drifts out of sync between the two — a
// missing entry causes the dev server to fall back to serving index.html
// for that API call (200 OK, HTML body), which downstream code then
// mis-parses as JSON, producing hard-to-diagnose runtime crashes.
const PROXIED_API_PREFIXES = [
  "/api",
  "/auth",
  "/dashboard",
  "/audit-dashboard",
  "/visits",
  "/patient-charts",
  "/patients",
  "/medications",
  "/agency-profile",
  "/benefits",
  "/bereavement-assessments",
  "/bereavement-letters",
  "/bereavement-poc",
  "/bereavement-support",
  "/billing",
  "/certifications",
  "/communications-log",
  "/documents",
  "/eligibility",
  "/f2f",
  "/fax",
  "/icd10",
  "/idg",
  "/lab-catalog",
  "/order-templates",
  "/patient-assignments",
  "/patient-issues",
  "/patient-orders",
  "/physician-orders",
  "/physicians",
  "/plan-of-care",
  "/post-death-bereavement",
  "/referrals",
  "/staff",
  "/vendors",
  "/visit-recordings",
];

function buildApiProxy() {
  return Object.fromEntries(
    PROXIED_API_PREFIXES.map((prefix) => [
      prefix,
      { target: apiTarget, changeOrigin: true },
    ]),
  );
}

export default defineConfig({
  root: frontendRoot,
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      // Precache ONLY the app shell (JS/CSS/HTML) so the SPA itself can
      // load with zero connectivity -- this deliberately does NOT cache
      // any API/data traffic. Caching patient chart data in the service
      // worker would risk an RN looking at stale clinical data without
      // realizing it; all API calls always go to the network (or into the
      // durable IndexedDB queue on failure -- see src/offline/), never to
      // a service-worker cache.
      workbox: {
        navigateFallback: "/index.html",
        // Never let workbox intercept API calls -- explicitly exclude
        // every backend prefix the proxy config above knows about, in
        // addition to the default precache-only behavior.
        navigateFallbackDenylist: [/^\/documents\//, /^\/visits\//, /^\/api\//],
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
      },
      manifest: {
        name: "SNS Hospice Solutions",
        short_name: "SNS EMR",
        start_url: "/login",
        display: "standalone",
        background_color: "#0b1220",
        theme_color: "#0b1220",
        icons: [],
      },
      // Service worker only ships in production builds. In dev, offline
      // capture/sync is still fully functional (see src/offline/) --
      // only the "load the app shell with zero connectivity" capability
      // requires the built/preview artifact.
      devOptions: { enabled: false },
    }),
  ],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setupTests.js",
  },
  resolve: {
    preserveSymlinks: true,
  },
  server: {
    port: 5173,
    host: true,
    proxy: buildApiProxy(),
  },
  preview: {
    port: 4173,
    host: true,
    allowedHosts: true,
    proxy: buildApiProxy(),
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
