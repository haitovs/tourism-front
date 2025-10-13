// Hide on scroll down, show on any scroll up (no need to reach top)
(function () {
    const header = document.querySelector(".detailbar");
    if (!header) return;

    let lastY = window.scrollY || window.pageYOffset;
    let ticking = false;

    // Tweak these if you like
    const HIDE_THRESHOLD = 8; // how much downward movement before hiding
    const SHOW_THRESHOLD = 1; // how much upward movement before showing

    function update() {
        ticking = false;

        const y = window.scrollY || window.pageYOffset;
        const delta = y - lastY;

        // Always show & clear styles when fully at top
        if (y <= 0) {
            header.classList.remove("detailbar--hidden");
            header.classList.remove("detailbar--scrolled");
            header.classList.add("detailbar--at-top");
            lastY = 0;
            return;
        }

        // When away from top, add scrolled styling once
        header.classList.add("detailbar--scrolled");
        header.classList.remove("detailbar--at-top");

        // Hide if scrolling down past threshold
        if (delta > HIDE_THRESHOLD) {
            header.classList.add("detailbar--hidden");
        }
        // Show immediately on any upward movement (tiny threshold)
        else if (delta < -SHOW_THRESHOLD) {
            header.classList.remove("detailbar--hidden");
        }

        // Always update lastY so tiny direction changes are detected quickly
        lastY = y;
    }

    function onScroll() {
        if (!ticking) {
            requestAnimationFrame(update);
            ticking = true;
        }
    }

    // Initial state
    update();

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", () => requestAnimationFrame(update), { passive: true });
})();
