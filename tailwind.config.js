/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        forest: { DEFAULT: '#163832', dark: '#0E2622', light: '#1F4D3A' },
        gold: { DEFAULT: '#C89B3C', light: '#E4C878' },
        clayred: '#8C2F39',
        sand: '#FBF8F2',
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"Inter"', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
