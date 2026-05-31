export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        finance: {
          blue: "#007bff",
          navy: "#111827",
          ink: "#1f2937",
          line: "#d6dde8",
          soft: "#f5f7fb"
        }
      },
      boxShadow: {
        dashboard: "0 14px 45px rgba(15, 23, 42, 0.10)"
      }
    }
  },
  plugins: []
};
