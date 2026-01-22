import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        dark: {
          bg: '#0a0a0b',
          card: '#111113',
          border: '#1f1f23',
          hover: '#18181b',
        },
        // Accent colors for visualization
        accent: {
          cyan: '#22d3ee',
          purple: '#a855f7',
          green: '#10b981',
          blue: '#3b82f6',
          orange: '#f97316',
        },
        // Node state colors
        node: {
          pending: '#9ca3af',
          active: '#3b82f6',
          complete: '#10b981',
          error: '#ef4444',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': {
            opacity: '1',
            filter: 'drop-shadow(0 0 8px currentColor)',
          },
          '50%': {
            opacity: '0.7',
            filter: 'drop-shadow(0 0 16px currentColor)',
          },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
