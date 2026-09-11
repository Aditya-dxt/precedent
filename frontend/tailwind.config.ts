import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#1B2A4A',
          50:  '#EEF1F7',
          100: '#C9D3E8',
          200: '#A4B4D9',
          300: '#7F96CA',
          400: '#5A78BB',
          500: '#3A5AA2',
          600: '#2E4883',
          700: '#233665',
          800: '#1B2A4A',
          900: '#111C32',
        },
        gold: {
          DEFAULT: '#C9922A',
          50:  '#FDF6E9',
          100: '#F8E5BF',
          200: '#F2CF8A',
          300: '#EBB855',
          400: '#E4A124',
          500: '#C9922A',
          600: '#A87523',
          700: '#87591B',
          800: '#663E14',
          900: '#45280C',
        },
        offwhite: '#F5F3EF',
        cream: '#FAF8F4',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        xl: '12px',
        '2xl': '16px',
      },
      boxShadow: {
        card: '0 2px 16px 0 rgba(27,42,74,0.08)',
        'card-hover': '0 8px 32px 0 rgba(27,42,74,0.14)',
      },
    },
  },
  plugins: [],
} satisfies Config
