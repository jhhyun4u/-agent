import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // ── 간격 체계 (8px 기반) ──
      spacing: {
        'xs': '0.375rem',   /* 6px */
        'sm': '0.5rem',     /* 8px */
        'md': '1rem',       /* 16px */
        'lg': '1.5rem',     /* 24px */
        'xl': '2rem',       /* 32px */
        '2xl': '3rem',      /* 48px */
        '3xl': '4rem',      /* 64px */
      },

      // ── 그림자 체계 ──
      boxShadow: {
        // 기존 Tailwind 그림자
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.3)',

        // 커스텀 그림자 (다크 모드)
        'elevation': '0 20px 25px -5px rgba(0, 0, 0, 0.4)',
        'card-hover': '0 20px 25px -5px rgba(62, 207, 142, 0.1)',
        'inset-light': 'inset 0 1px 2px rgba(255, 255, 255, 0.05)',
      },

      // ── 색상 확장 ──
      colors: {
        'surface': {
          DEFAULT: '#111111',
          secondary: '#1c1c1c',
          tertiary: '#262626',
        },
        'accent-green': {
          DEFAULT: '#3ecf8e',
          dark: '#2d9966',
          light: '#4fd99e',
        },
      },

      // ── 애니메이션 ──
      animation: {
        'fadeIn': 'fadeIn 200ms ease-in-out',
        'slideInUp': 'slideInUp 300ms ease-out',
        'slideInDown': 'slideInDown 300ms ease-out',
      },

      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideInUp: {
          from: {
            opacity: '0',
            transform: 'translateY(10px)',
          },
          to: {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideInDown: {
          from: {
            opacity: '0',
            transform: 'translateY(-10px)',
          },
          to: {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
      },

      // ── 전환 타이밍 ──
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
    },
  },
  plugins: [],
};
export default config;
