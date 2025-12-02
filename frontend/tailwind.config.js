/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['Menlo', 'Courier New', 'monospace'],
      },
      colors: {
        nyc: {
          black: '#000000',
          dark: '#121212',
          panel: '#1E1E1E',
          border: '#333333',
          text: '#E0E0E0',
          muted: '#888888',
          blue: '#0039A6',   // A/C/E Lines
          orange: '#FF6319', // B/D/F/M
          green: '#00933C',  // 4/5/6
          red: '#EE352E',    // 1/2/3
          yellow: '#FCCC0A', // N/Q/R/W
          gray: '#A7A9AC',   // L
        }
      }
    },
  },
  plugins: [],
}