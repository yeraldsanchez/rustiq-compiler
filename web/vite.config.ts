import { defineConfig } from "vite";

const API = "http://localhost:8000";

export default defineConfig({
  base: "./",
  server: {
    // Los ejemplos se leen de tests/, fuera de web/ (ruta relativa a web/).
    fs: { allow: [".."] },
    // En desarrollo, uvicorn corre aparte y Vite le reenvía la API.
    proxy: { "/compile": API },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    // CodeMirror completo pesa ~520 kB sin comprimir; se sirve en local.
    chunkSizeWarningLimit: 700,
  },
});
