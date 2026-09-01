/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#ffffff',
        surface: '#f8fafc', // slate-50
        border: '#e2e8f0', // slate-200
        text: '#0f172a', // slate-900
        textMuted: '#64748b', // slate-500
        primary: '#2563eb', // blue-600
        primaryHover: '#1d4ed8', // blue-700
        success: '#16a34a', // green-600
        successBg: '#dcfce7', // green-100
        warning: '#d97706', // amber-600
        warningBg: '#fef3c7', // amber-100
        critical: '#dc2626', // red-600
        criticalBg: '#fee2e2', // red-100
      }
    },
  },
  plugins: [],
}
