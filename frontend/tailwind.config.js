/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        manga: {
          dark: '#121316',
          panel: '#1a1c23',
          border: '#2a2e3d',
          accent: '#6366f1',
          accentHover: '#4f46e5',
        }
      }
    },
  },
  plugins: [],
}
