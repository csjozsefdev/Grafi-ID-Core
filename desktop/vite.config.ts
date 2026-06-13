import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    headers: {
      "Cache-Control": "no-store",
    },
    // Vite must not watch Rust build output (Windows EBUSY on locked .exe files).
    watch: {
      ignored: [
        "**/src-tauri/target/**",
        "**/src-tauri/runtime/**",
        "**/src-tauri/gen/**",
      ],
    },
  },
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    target: "es2020",
    minify: !process.env.TAURI_DEBUG ? "esbuild" : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
});
