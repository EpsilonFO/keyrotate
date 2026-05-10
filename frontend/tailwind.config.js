/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1a1a1a",
        muted: "#666666",
        bg: "#f8f5ef",
        card: "#fffdf8",
        line: "#e6e0d3",
        royal: {
          DEFAULT: "#1d3a8a",
          dark: "#15296a",
          light: "#2d52b8",
        },
        terracotta: {
          DEFAULT: "#c75d3a",
          dark: "#a84a2d",
        },
      },
      fontFamily: {
        serif: ["'Cormorant Garamond'", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      transitionDuration: {
        DEFAULT: "400ms",
      },
    },
  },
  plugins: [],
};
