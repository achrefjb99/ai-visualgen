/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts,scss}",
  ],
  theme: {
    extend: {
      colors: {
        kids: {
          primary: {
            DEFAULT: '#38BDF8', // Bleu ciel joyeux (Sky 400)
            light: '#BAE6FD',   // Ciel pastel doux (Sky 200)
            dark: '#0284C7',    // Bleu océan profond (Sky 600)
          },
          secondary: {
            DEFAULT: '#FBBF24', // Jaune soleil radieux (Amber 400)
            light: '#FEF08A',   // Jaune poussin délicat (Yellow 200)
            dark: '#D97706',    // Or ambré chaud (Amber 600)
          },
          success: {
            DEFAULT: '#34D399', // Vert prairie pétillant (Emerald 400)
            light: '#A7F3D0',   // Menthe pastel douce (Emerald 200)
            dark: '#059669',    // Vert forêt profond (Emerald 600)
          },
          accent: {
            coral: '#FB7185',   // Corail dynamique (Rose 400)
            purple: '#A78BFA',  // Lilas magique (Violet 400)
            orange: '#FB923C',  // Orange mandarine joyeux (Orange 400)
          },
          dark: {
            DEFAULT: '#1E293B', // Texte ardoise sombre très lisible (Slate 800)
            muted: '#64748B',   // Texte secondaire doux (Slate 500)
          },
          surface: {
            DEFAULT: '#FFFFFF', // Blanc éclatant
            soft: '#F8FAFC',    // Fond d'écran doux légèrement bleuté (Slate 50)
            card: '#F0F9FF',    // Ciel très pastel pour les cartes (Sky 50)
          },
          themes: {
            dino: '#10B981',    // Vert dinosaure
            space: '#6366F1',   // Bleu indigo galactique
            nature: '#F59E0B',  // Jaune miel savane
          },
        },
      },
      fontFamily: {
        kids: ['Fredoka', 'Nunito', 'sans-serif'],
        body: ['Nunito', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
        'full': '9999px',
      },
      boxShadow: {
        'kids-soft': '0 10px 25px -5px rgba(56, 189, 248, 0.15), 0 8px 10px -6px rgba(56, 189, 248, 0.1)',
        'kids-card': '0 12px 24px -4px rgba(30, 41, 59, 0.08), 0 4px 6px -2px rgba(30, 41, 59, 0.04)',
        'kids-button': '0 6px 0 0 #0284C7',
        'kids-button-secondary': '0 6px 0 0 #D97706',
        'kids-button-accent': '0 6px 0 0 #E11D48',
        'kids-button-success': '0 6px 0 0 #059669',
        'kids-floating': '0 20px 30px -10px rgba(0, 0, 0, 0.12)',
      },
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        bounceSmall: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        wiggle: 'wiggle 1s ease-in-out infinite',
        'bounce-soft': 'bounceSmall 2s infinite ease-in-out',
      },
    },
  },
  plugins: [],
};
