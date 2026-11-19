import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, ".", "");
    return {
        base: env.VITE_BASE_PATH || "/",
        plugins: [react()],
        build: {
            rollupOptions: {
                output: {
                    manualChunks: {
                        react: ["react", "react-dom", "react-router-dom"],
                        charts: ["recharts"],
                        query: ["@tanstack/react-query"],
                        icons: ["lucide-react"],
                    },
                },
            },
        },
        server: {
            port: 5173,
            proxy: {
                "/api": {
                    target: "http://localhost:8000",
                    changeOrigin: true,
                },
                "/analytics": {
                    target: "http://localhost:8001",
                    changeOrigin: true,
                    rewrite: function (path) { return path.replace(/^\/analytics/, ""); },
                },
            },
        },
    };
});
