// tailwind.config.js
module.exports = {
    content: ["./app/templates/**/*.html", "./app/static/js/**/*.js", "./app/**/*.py"],
    theme: {
        extend: {
            // Define once — this includes your custom shadow
            boxShadow: {
                soft: "0 10px 30px rgba(0,0,0,0.08)",
            },

            // Font families shorthand
            fontFamily: {
                mont: ["Montserrat", "ui-sans-serif", "system-ui"],
                roboto: ["Roboto", "ui-sans-serif", "system-ui"],
                inter: ["Inter", "ui-sans-serif", "system-ui"],
                lato: ["Inter", "ui-sans-serif", "system-ui"],
            },
        },
    },

    safelist: [
        // arbitrary values you use:
        { pattern: /rounded-\[.*\]/ },
        { pattern: /grid-cols-\[.*\]/ },
        { pattern: /bg-\[.*\]/ },
        { pattern: /text-\[.*\]/ },

        // utilities you use conditionally
        { pattern: /line-clamp-\d+/ },
        { pattern: /(xl|lg|md|sm):flex-row/ },
        { pattern: /(xl|lg|md|sm):grid-cols-\[.*\]/ },
        { pattern: /max-w-\[.*\]/ },
        "shadow-soft",
    ],
};
