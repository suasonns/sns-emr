import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ✅ ENTERPRISE SPA ROUTING SAFE CONFIG
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    host: true,

    // ✅ THIS IS THE FIX FOR /billing 404
    historyApiFallback: true,
  },
});
