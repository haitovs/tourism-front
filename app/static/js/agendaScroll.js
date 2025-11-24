// Drag-to-scroll for agenda day pills (without blocking clicks)
(function () {
    const scrollers = document.querySelectorAll(".agenda-day-scroller");
    scrollers.forEach((el) => {
        let active = false;
        let startX = 0;
        let startScroll = 0;

        const onDown = (e) => {
            // ignore clicks on the pill buttons so selection still works
            if (e.button !== 0) return;
            if (e.target && e.target.closest("button")) return;

            active = true;
            startX = e.pageX - el.offsetLeft;
            startScroll = el.scrollLeft;
            el.classList.add("is-dragging");
        };

        const onMove = (e) => {
            if (!active) return;
            const x = e.pageX - el.offsetLeft;
            const dx = x - startX;
            el.scrollLeft = startScroll - dx;
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
    });
})();
