/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f3f3ff',
          100: '#cacafd',
          500: '#2424ff',
          600: '#1a1aff',
          700: '#1010e6',
        },
        accent: {
          500: '#f15a24',
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
      },
      boxShadow: {
        'premium': '0 10px 30px rgba(0, 0, 0, 0.03), 0 1px 8px rgba(0, 0, 0, 0.02)',
        'premium-lg': '0 20px 40px rgba(0, 0, 0, 0.04), 0 1px 12px rgba(0, 0, 0, 0.03)',
        'brand-glow': '0 10px 20px rgba(37, 99, 235, 0.1)',
        'alert-glow': '0 0 15px rgba(239, 68, 68, 0.3)',
        'success-glow': '0 0 15px rgba(16, 185, 129, 0.3)',
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(15px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
