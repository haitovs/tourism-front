// Drag-to-scroll for agenda day pills (allowing clicks)
(function () {
    const scrollers = document.querySelectorAll(".agenda-day-scroller");
    scrollers.forEach((el) => {
        let active = false;
        let startX = 0;
        let startScroll = 0;
        let moved = false;
        const DRAG_THRESHOLD = 3; // pixels before we treat as drag

        const onDown = (e) => {
            if (e.button !== 0) return;
            // If the user starts on a pill button, let the native click work.
            if (e.target && e.target.closest("button")) return;

            active = true;
            moved = false;
            startX = e.clientX;
            startScroll = el.scrollLeft;
            el.classList.add("is-dragging");
        };

        const onMove = (e) => {
            if (!active) return;
            const dx = e.clientX - startX;
            if (Math.abs(dx) > DRAG_THRESHOLD) {
                moved = true;
                el.scrollLeft = startScroll - dx;
                e.preventDefault();
            }
        };

        const onUp = () => {
            if (!active) return;
            active = false;
            el.classList.remove("is-dragging");
        };

        el.addEventListener("pointerdown", onDown);
        el.addEventListener("pointermove", onMove);
        el.addEventListener("pointerup", onUp);
        el.addEventListener("pointerleave", onUp);

        // Support mouse wheel to scroll horizontally
        el.addEventListener(
            "wheel",
            (e) => {
                if (Math.abs(e.deltaX) + Math.abs(e.deltaY) === 0) return;
                el.scrollLeft += (Math.abs(e.deltaY) > Math.abs(e.deltaX) ? e.deltaY : e.deltaX);
                e.preventDefault();
            },
            { passive: false }
        );
    });
})();
