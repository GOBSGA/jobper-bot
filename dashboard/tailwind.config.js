/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Brand: deep calm indigo — replaces orange entirely
        brand: {
          50:  "#EDEFFE",
          100: "#DADDFD",
          200: "#B6BDFC",
          300: "#8D98F9",
          400: "#6472F5",
          500: "#4A58EE",   // primary
          600: "#3846D6",   // hover
          700: "#2C37B8",
          800: "#222D96",
          900: "#1A2478",
        },
        // Accent: soft emerald for success/positive
        accent: {
          50:  "#EDFDF5",
          100: "#D3FAE8",
          200: "#A7F4D1",
          300: "#6BE8B2",
          400: "#2ED48D",
          500: "#10BC72",
          600: "#0A9A5C",
          700: "#087C4A",
          800: "#086339",
          900: "#07512E",
        },
        // Surface neutrals — the calm foundation
        surface: {
          bg:     "#F5F6FA",   // app background
          card:   "#FFFFFF",
          border: "#E3E5EC",   // default border
          hover:  "#F0F1F7",   // hover state bg
        },
        // Ink scale — text hierarchy
        ink: {
          900: "#0D0E14",  // primary text
          600: "#5A5B6A",  // secondary
          400: "#9394A5",  // placeholder / muted
          200: "#C9CAD8",  // disabled
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      letterSpacing: {
        tighter: "-0.025em",
        snug:    "-0.012em",
      },
      boxShadow: {
        // Very restrained shadows
        "xs":  "0 1px 2px 0 rgb(0 0 0 / 0.04)",
        "sm":  "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        "md":  "0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.04)",
        "card":"0 0 0 1px #E3E5EC",  // border-only shadow — zero elevation noise
        "none":"none",
      },
      borderRadius: {
        "xl":  "0.75rem",
        "2xl": "1rem",
        "3xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
