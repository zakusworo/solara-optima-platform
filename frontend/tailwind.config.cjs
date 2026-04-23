/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F5F0E8',
        'background-secondary': '#FDFAF4',
        'background-tertiary': '#EDE8DC',
        border: '#C8BFA8',
        text: '#2C2418',
        'text-secondary': '#5A4E3A',
        'text-muted': '#8A7A60',
        accent: '#4A8C20',
        'accent-hover': '#3A7010',
        green: '#3A7A18',
        amber: '#A07010',
        red: '#B04030',
        purple: '#5A7A30',
      },
      fontFamily: {
        sans: ['Lora', 'serif'],
        mono: ['Source Code Pro', 'monospace'],
      },
    },
  },
  plugins: [],
}
