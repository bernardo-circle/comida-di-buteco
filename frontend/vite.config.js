import fs from "node:fs/promises";
import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
    {
      name: "buteco-data-api",
      configureServer(server) {
        server.middlewares.use("/api/butecos", async (_req, res) => {
          const datasetPath = path.resolve(__dirname, "../output/rio_butecos_final.json");

          try {
            const content = await fs.readFile(datasetPath, "utf-8");
            res.setHeader("Content-Type", "application/json");
            res.end(content);
          } catch {
            res.statusCode = 404;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ error: "Dataset not found" }));
          }
        });
      },
    },
  ],
});
