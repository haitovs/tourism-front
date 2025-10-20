(function () {
    function toPx(el, val) {
        if (!val) return 16;
        if (/px$/i.test(val)) return parseFloat(val);
        const test = document.createElement("div");
        test.style.position = "absolute";
        test.style.visibility = "hidden";
        test.style.width = val;
        el.appendChild(test);
        const px = test.getBoundingClientRect().width || test.offsetWidth || 0;
        el.removeChild(test);
        return px || 16;
    }

    function gapPx(root) {
        const raw = getComputedStyle(root).getPropertyValue("--gap").trim() || "16px";
        return toPx(document.body, raw);
    }

    function buildUnit(viewport, baseNodes, gap) {
        const meas = document.createElement("ul");
        meas.style.cssText =
            "display:flex;gap:0;visibility:hidden;position:absolute;left:-99999px;top:0;margin:0;padding:0;list-style:none";
        document.body.appendChild(meas);

        const unit = [];
        const add = () => baseNodes.forEach((n) => unit.push(n.cloneNode(true)));
        add();

        const vw = Math.max(1, viewport.getBoundingClientRect().width);

        const measure = () => {
            meas.innerHTML = "";
            unit.forEach((n) => meas.appendChild(n.cloneNode(true)));
            const ch = [...meas.children];
            const w = ch.reduce((a, el) => a + el.getBoundingClientRect().width, 0);
            // include *internal* gaps within the unit
            return w + Math.max(0, ch.length - 1) * gap;
        };

        let uw = measure();
        // pad until > viewport (extra 10% for safety)
        while (uw < vw * 1.1) {
            add();
            uw = measure();
        }
        document.body.removeChild(meas);
        return { unit, unitWidth: uw };
    }

    function initOne(root) {
        const viewport = root.querySelector(".marquee__viewport");
        const track = root.querySelector(".marquee__track");
        if (!viewport || !track) return;

        const min = Number(root.dataset.min || 0);
        const speed = Number(root.dataset.speed || 60);
        const respectRM = (root.dataset.respectRm || "false").toLowerCase() === "true";
        const reduce = respectRM && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        const base = [...track.children];
        if (base.length < min) return;

        // prepare
        let g = gapPx(root);
        track.innerHTML = "";

        let { unit, unitWidth } = buildUnit(viewport, base, g);
        if (!unitWidth) {
            requestAnimationFrame(() => initOne(root));
            return; // layout not ready
        }

        // We render TWO units separated by CSS gap.
        // The visible cycle therefore equals unitWidth + one extra gap between the two units.
        let cycle = unitWidth + g;

        // mount two copies
        const f1 = document.createDocumentFragment();
        const f2 = document.createDocumentFragment();
        unit.forEach((n) => f1.appendChild(n.cloneNode(true)));
        unit.forEach((n) => f2.appendChild(n.cloneNode(true)));
        track.appendChild(f1);
        track.appendChild(f2);

        // styling
        const gapCss = getComputedStyle(root).getPropertyValue("--gap").trim() || "16px";
        track.style.display = "flex";
        track.style.gap = gapCss;
        track.style.willChange = "transform";
        track.style.userSelect = "none";
        track.style.pointerEvents = "auto";

        // animation
        let last = performance.now();
        let offset = 0;

        // subpixel-friendly transform (align to device pixel)
        const toPxAligned = (x) => {
            const dpr = window.devicePixelRatio || 1;
            return Math.round(x * dpr) / dpr;
        };

        function loop(now) {
            const dt = (now - last) / 1000;
            last = now;

            if (!reduce) {
                offset += speed * dt;
                if (cycle > 0) {
                    // use cycle (unitWidth + inter-unit gap) for a perfect seamless loop
                    const m = offset % cycle;
                    const tx = -toPxAligned(m);
                    track.style.transform = `translate3d(${tx}px,0,0)`;
                }
            } else {
                track.style.transform = "translate3d(0,0,0)";
            }
            requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);

        // Rebuild on resize or when container/gap changes
        const ro = new ResizeObserver(() => {
            // remember current progress within cycle
            const cur = cycle > 0 ? offset % cycle : 0;

            // recompute gap (could change with CSS)
            g = gapPx(root);

            // rebuild unit for new viewport/gap
            track.innerHTML = "";
            const rebuilt = buildUnit(viewport, base, g);
            unit = rebuilt.unit;
            unitWidth = rebuilt.unitWidth || unitWidth;
            cycle = unitWidth + g;

            const nf1 = document.createDocumentFragment();
            const nf2 = document.createDocumentFragment();
            unit.forEach((n) => nf1.appendChild(n.cloneNode(true)));
            unit.forEach((n) => nf2.appendChild(n.cloneNode(true)));
            track.appendChild(nf1);
            track.appendChild(nf2);

            // keep same visual progress
            offset = cur;
            const tx = -toPxAligned(offset % cycle);
            track.style.gap = getComputedStyle(root).getPropertyValue("--gap").trim() || "16px";
            track.style.transform = `translate3d(${tx}px,0,0)`;
        });
        ro.observe(viewport);
    }

    function initGroup(group) {
        group.querySelectorAll("[data-marquee]").forEach(initOne);
    }

    window.addEventListener("load", () => {
        document.querySelectorAll("[data-marquee]:not([data-marquee-group] [data-marquee])").forEach(initOne);
        document.querySelectorAll("[data-marquee-group]").forEach(initGroup);
    });
})();
