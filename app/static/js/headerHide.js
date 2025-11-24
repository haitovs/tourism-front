// app/static/js/headerHide.js
// Sticky detailbar that hides on downward scroll and reappears on upward scroll.
(function () {
    const header = document.getElementById("site-header");
    if (!header) return;

    const scrollRoot = document.scrollingElement || document.documentElement || document.body;
    const spacer = document.getElementById("detailbar-spacer");
    const getScrollY = () => {
        if (typeof window.scrollY === "number") return window.scrollY;
        if (typeof window.pageYOffset === "number") return window.pageYOffset;
        if (scrollRoot && typeof scrollRoot.scrollTop === "number") return scrollRoot.scrollTop;
        return document.body ? document.body.scrollTop : 0;
    };

    const TOP_LOCK = 4;    // force header visible near top
    const HIDE_DELTA = 12; // minimum downward movement before hide
    const SHOW_DELTA = 2;  // minimum upward movement before show

    let state = "visible"; // "visible" | "hidden"
    let lastY = getScrollY();
    let ticking = false;

    const syncSpacer = () => {
        if (!spacer) return;
        const rect = header.getBoundingClientRect();
        spacer.style.height = `${rect.height}px`;
    };

    const scheduleSpacerSync = () => {
        if (spacer) requestAnimationFrame(syncSpacer);
    };

    const applyVisible = (atTop = false) => {
        header.classList.remove("detailbar--hidden");
        header.classList.toggle("detailbar--at-top", atTop);
        if (!atTop) {
            header.classList.add("detailbar--scrolled");
        } else {
            header.classList.remove("detailbar--scrolled");
        }
        state = "visible";
        lastY = getScrollY();
        scheduleSpacerSync();
    };

    const applyHidden = () => {
        header.classList.add("detailbar--hidden");
        header.classList.remove("detailbar--at-top");
        header.classList.add("detailbar--scrolled");
        state = "hidden";
        scheduleSpacerSync();
    };

    function update() {
        ticking = false;
        const y = Math.max(0, getScrollY());

        if (y <= TOP_LOCK) {
            applyVisible(true);
            lastY = y;
            return;
        }

        const delta = y - lastY;

        if (state === "visible") {
            if (delta > HIDE_DELTA) {
                applyHidden();
            } else {
                header.classList.remove("detailbar--at-top");
                header.classList.add("detailbar--scrolled");
            }
        } else if (delta < -SHOW_DELTA) {
            applyVisible(false);
        }

        lastY = y;
    }

    function onScroll() {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(update);
        }
    }

    const onResize = () => {
        scheduleSpacerSync();
        requestAnimationFrame(update);
    };

    update();
    scheduleSpacerSync();
    window.addEventListener("load", scheduleSpacerSync);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
})();
