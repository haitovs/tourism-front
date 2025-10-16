// tailwind.config.js (CommonJS works well with the EXE)
module.exports = {
    content: ["./app/templates/**/*.html", "./app/static/js/**/*.js", "./app/**/*.py"],
    theme: {
        extend: {
            // You use `shadow-soft` in templates; define it here
            boxShadow: {
                soft: "0 10px 30px rgba(0,0,0,0.08)",
            },

            // Helpful shorthands so you can use `font-mont` / `font-roboto` if you want
            fontFamily: {
                mont: ["Montserrat", "ui-sans-serif", "system-ui"],
                roboto: ["Roboto", "ui-sans-serif", "system-ui"],
            },

            boxShadow: { soft: "0 10px 30px rgba(0,0,0,.08)" },
        },
    },

    // Ensure dynamic/rare classes are kept
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
        "shadow-soft",
    ],
};
