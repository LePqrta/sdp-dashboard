import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1c2430",
        muted: "#6b7280",
        panel: "#fffdf7",
        line: "#dbe5dc",
        accent: "#2f7d78",
        success: "#2f7d78",
        warning: "#d99145",
        orchid: "#7f69ab",
        mint: "#84ccc5",
        vellum: "#f6f1e6",
      },
      boxShadow: {
        soft: "0 18px 48px rgba(50, 61, 73, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
