import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" so the static build in dist/ works from any folder (GitHub Pages, an artifact, a file share)
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: { output: { manualChunks: { echarts: ["echarts/core", "echarts/charts", "echarts/components", "echarts/renderers"] } } },
  },
});
