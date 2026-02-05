/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fdf4f0",
          100: "#fbe6dc",
          200: "#f7c9b5",
          300: "#f2a585",
          400: "#ec7d51",
          500: "#e85d2a",
          600: "#d44a1a",
          700: "#b03a15",
          800: "#8d3118",
          900: "#742c18",
        },
        accent: {
          50: "#f0fdf6",
          100: "#dbfce8",
          200: "#b9f7d3",
          300: "#83f0b1",
          400: "#46e085",
          500: "#1ec963",
          600: "#12a74e",
          700: "#128440",
          800: "#146836",
          900: "#12552e",
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
