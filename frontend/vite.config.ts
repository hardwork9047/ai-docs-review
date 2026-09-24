/// <reference types="vitest/config" />
import { defineConfig } from "vite";

export default defineConfig({
  // 開発時は backend(make dev-backend)へ /api を中継する
  server: { proxy: { "/api": "http://localhost:8000" } },
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
});
