import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        mint: "#2eb67d",
        coral: "#f9735b",
        cloud: "#f7f9fb",
      },
    },
  },
  plugins: [],
};

export default config;
