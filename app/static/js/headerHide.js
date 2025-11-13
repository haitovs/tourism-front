// app/static/js/headerHide.js
// Hide header when scrolling down; show as soon as the user scrolls up (by ~1px).
(function () {
    const header = document.getElementById("site-header"); // single source of truth
    if (!header) return;

    const scrollRoot = document.scrollingElement || document.documentElement || document.body;
    const getScrollY = () => {
        if (typeof window.scrollY === "number") return window.scrollY;
        if (typeof window.pageYOffset === "number") return window.pageYOffset;
        if (scrollRoot && typeof scrollRoot.scrollTop === "number") return scrollRoot.scrollTop;
        return document.body ? document.body.scrollTop : 0;
    };

    let lastY = getScrollY();
    let ticking = false;

    const HIDE_DELTA = 6; // how much down-movement before hide
    const SHOW_DELTA = 1; // how much up-movement before show
    const TOP_LOCK = 0; // y<=TOP_LOCK => force visible & reset state

    function update() {
        ticking = false;
        const y = Math.max(0, getScrollY());
        const delta = y - lastY;

        // Fully at top: reset styles and show header
        if (y <= TOP_LOCK) {
            header.classList.remove("detailbar--hidden", "detailbar--scrolled");
            header.classList.add("detailbar--at-top");
            lastY = 0;
            return;
        }

        // Mark scrolled state (shadow/blur) once away from top
        header.classList.add("detailbar--scrolled");
        header.classList.remove("detailbar--at-top");

        // Downward movement beyond threshold => hide
        if (delta > HIDE_DELTA) {
            header.classList.add("detailbar--hidden");
            lastY = y;
            return;
        }

        // Any tiny upward movement => show
        if (delta < -SHOW_DELTA) {
            header.classList.remove("detailbar--hidden");
            lastY = y;
            return;
        }

        // keep tracking to react quickly to next small change
        lastY = y;
    }

    function onScroll() {
        if (!ticking) {
            requestAnimationFrame(update);
            ticking = true;
        }
    }

    // Init now and on changes
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", () => requestAnimationFrame(update));
})();
