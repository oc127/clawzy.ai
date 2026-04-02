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
        brand: {
          DEFAULT: '#E63946',
          50: '#FDE8EA',
          100: '#FBD1D5',
          200: '#F7A3AB',
          300: '#F27580',
          400: '#EE4756',
          500: '#E63946',
          600: '#C41D2A',
          700: '#931620',
          800: '#620E15',
          900: '#31070B',
        },
        surface: {
          DEFAULT: '#0A0A0A',
          50: '#2A2A2A',
          100: '#1A1A1A',
          200: '#141414',
          300: '#0F0F0F',
          400: '#0A0A0A',
        },
      },
    },
  },
  plugins: [],
}
export default config
