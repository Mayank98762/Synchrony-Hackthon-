import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The data is imported from the pipeline's own outputs (../dashboard/public/data, ../outputs), so the dev
// server must be allowed to read the repo root. base "./" keeps the static build portable.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: { fs: { allow: [".."] } },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: { output: { manualChunks: { echarts: ["echarts/core", "echarts/charts", "echarts/components", "echarts/renderers"] } } },
  },
});
