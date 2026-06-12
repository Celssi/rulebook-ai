/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        surface: "#0f1218",
        panel: "#161b24",
        elevated: "#1e2532",
        border: "#2a3344",
        muted: "#8b95a8",
        accent: {
          DEFAULT: "#d4a24c",
          muted: "#3d3528",
        },
        moss: {
          DEFAULT: "#6b8f71",
          muted: "#2a3d2e",
        },
        stat: {
          health: "#e05a5a",
          morale: "#6b9fff",
          supplies: "#d4a24c",
        },
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            "--tw-prose-body": theme("colors.gray.200"),
            "--tw-prose-headings": theme("colors.gray.100"),
            "--tw-prose-links": theme("colors.accent.DEFAULT"),
            "--tw-prose-bold": theme("colors.gray.100"),
            "--tw-prose-code": theme("colors.accent.DEFAULT"),
            maxWidth: "none",
          },
        },
      }),
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
