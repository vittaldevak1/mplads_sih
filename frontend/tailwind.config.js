/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          950: '#F8FAFC',
          900: '#F1F5F9',
          800: '#E2E8F0',
          700: '#CBD5E1',
          600: '#94A3B8',
          500: '#64748B',
          400: '#475569',
          300: '#334155',
          200: '#1E293B',
          100: '#0F172A',
          50: '#FFFFFF',
        },
        accent: {
          DEFAULT: '#1E3A8A',
          light: '#2563EB',
          dark: '#1E3A5C',
        },
        risk: {
          critical: '#DC2626',
          high: '#D97706',
          medium: '#2563EB',
          low: '#16A34A',
        },
      },
      fontFamily: {
        serif: ['Merriweather', 'serif'],
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
