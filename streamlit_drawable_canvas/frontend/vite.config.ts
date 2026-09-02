import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  // Streamlit serves the built component from /component/<name>/, so every asset
  // reference has to be relative. This replaces CRA's "homepage": "." setting.
  base: "./",
  build: {
    outDir: "build",
    // The Python side ships this directory verbatim; keep it clean between builds.
    emptyOutDir: true,
  },
  server: {
    port: 3001,
  },
})
