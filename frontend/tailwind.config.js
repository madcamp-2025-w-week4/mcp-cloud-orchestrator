/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // AWS Console Style Colors
                'aws-navy': '#232f3e',
                'aws-orange': '#ff9900',
                'aws-dark': '#1a1a2e',
                'aws-light': '#f5f5f5',
            },
            fontFamily: {
                'sans': ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
