/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        forge: {
          bg: '#0a0a0f',
          surface: '#111118',
          border: '#1e1e2e',
          muted: '#2a2a3e',
          accent: '#6366f1',
          'accent-bright': '#818cf8',
          'accent-glow': 'rgba(99,102,241,0.15)',
          text: '#e2e8f0',
          subtle: '#64748b',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          easy: '#10b981',
          medium: '#f59e0b',
          hard: '#ef4444',
        }
      },
    },
  },
  plugins: [],
}