// Toggle the floating button and smooth-scroll to top
(function () {
    const btn = document.getElementById("to-top");
    if (!btn) return;

    const SHOW_AFTER = 300; // px scrolled before showing the button
    const icon = btn.querySelector(".to-top__icon");
    if (icon) {
        icon.style.transition = "opacity 140ms ease-out, transform 140ms ease-out";
        icon.style.opacity = "0";
        icon.style.transform = "translateY(6px)";
    }

    let ticking = false;

    function update() {
        ticking = false;
        const y = window.scrollY || window.pageYOffset;
        if (y > SHOW_AFTER) {
            btn.classList.add("to-top--show");
            if (icon) {
                icon.style.opacity = "1";
                icon.style.transform = "translateY(0)";
            }
        } else {
            btn.classList.remove("to-top--show");
            if (icon) {
                icon.style.opacity = "0";
                icon.style.transform = "translateY(6px)";
            }
        }
    }

    function onScroll() {
        if (!ticking) {
            requestAnimationFrame(update);
            ticking = true;
        }
    }

    // Click/keyboard → scroll to top
    function goTop() {
        const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (reduce) {
            window.scrollTo(0, 0);
        } else {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    }

    btn.addEventListener("click", goTop);
    btn.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            goTop();
        }
    });

    // Init
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", () => requestAnimationFrame(update), { passive: true });
})();
