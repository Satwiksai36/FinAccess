/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
        extend: {
            colors: {
                // Dark Navy Base
                bg: '#06080F',
                bgCard: '#0D1117',
                bgElevated: '#141B26',
                bgHighlight: '#1C2536',
                // Borders
                borderDim: 'rgba(255,255,255,0.05)',
                borderMid: 'rgba(255,255,255,0.10)',
                borderBright: 'rgba(255,255,255,0.18)',
                // Primary Emerald
                primary: '#00E5A0',
                primaryDark: '#00C48A',
                primaryGlow: 'rgba(0,229,160,0.25)',
                // Secondary Electric Blue
                blue: '#4F7CFF',
                blueGlow: 'rgba(79,124,255,0.2)',
                // Status Colors
                success: '#22C55E',
                warning: '#F59E0B',
                danger: '#F87171',
                // Text
                textPrimary: '#EDF2F7',
                textSecondary: '#8892A4',
                textFaint: '#4B5563',
            },
            fontFamily: {
                sans: ['Montserrat', 'sans-serif'],
                mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
            },
            backgroundImage: {
                'hero-gradient': 'radial-gradient(ellipse at 60% 0%, rgba(0,229,160,0.12) 0%, transparent 60%), radial-gradient(ellipse at 10% 80%, rgba(79,124,255,0.1) 0%, transparent 60%), linear-gradient(180deg, #06080F 0%, #0A0F1A 100%)',
                'card-glow': 'linear-gradient(135deg, rgba(0,229,160,0.04) 0%, rgba(79,124,255,0.03) 100%)',
                'primary-gradient': 'linear-gradient(135deg, #00E5A0, #00C48A)',
                'blue-gradient': 'linear-gradient(135deg, #4F7CFF, #3B5FD4)',
                'shimmer': 'linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent)',
            },
            boxShadow: {
                'card': '0 1px 2px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)',
                'card-hover': '0 4px 20px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,229,160,0.15)',
                'glow-primary': '0 0 24px rgba(0,229,160,0.3)',
                'glow-blue': '0 0 24px rgba(79,124,255,0.3)',
                'btn-primary': '0 0 20px rgba(0,229,160,0.35), 0 4px 12px rgba(0,0,0,0.5)',
                'inner-border': 'inset 0 0 0 1px rgba(255,255,255,0.08)',
            },
        },
    },
    plugins: [],
}
