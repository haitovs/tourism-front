(function () {
    function toPx(el, val) {
        if (!val) return 16;
        if (/px$/i.test(val)) return parseFloat(val);
        const test = document.createElement("div");
        test.style.position = "absolute";
        test.style.visibility = "hidden";
        test.style.width = val; // accepts rem, em, etc.
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
            return w + Math.max(0, ch.length - 1) * gap;
        };

        let uw = measure();
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
        const base = [...track.children];
        if (base.length < min) return;

        const g = gapPx(root);
        track.innerHTML = "";

        let { unit, unitWidth } = buildUnit(viewport, base, g);
        if (!unitWidth) {
            requestAnimationFrame(() => initOne(root));
            return;
        } // layout not ready yet

        const f1 = document.createDocumentFragment(),
            f2 = document.createDocumentFragment();
        unit.forEach((n) => f1.appendChild(n.cloneNode(true)));
        unit.forEach((n) => f2.appendChild(n.cloneNode(true)));
        track.appendChild(f1);
        track.appendChild(f2);

        track.style.display = "flex";
        track.style.gap = getComputedStyle(root).getPropertyValue("--gap").trim() || "16px";
        track.style.willChange = "transform";
        track.style.userSelect = "none";
        track.style.pointerEvents = "auto";

        const respectRM = (root.dataset.respectRm || "false").toLowerCase() === "true";
        const reduce = respectRM && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        let last = performance.now(),
            offset = 0;

        function loop(now) {
            const dt = (now - last) / 1000;
            last = now;
            if (!reduce) {
                offset += speed * dt;
                if (unitWidth > 0) {
                    const m = offset % unitWidth;
                    track.style.transform = `translate3d(${-m}px,0,0)`;
                }
            } else {
                track.style.transform = "translate3d(0,0,0)";
            }
            requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);

        const ro = new ResizeObserver(() => {
            const cur = unitWidth ? offset % unitWidth : 0;
            track.innerHTML = "";
            const rebuilt = buildUnit(viewport, base, g);
            unit = rebuilt.unit;
            unitWidth = rebuilt.unitWidth || unitWidth;
            const nf1 = document.createDocumentFragment(),
                nf2 = document.createDocumentFragment();
            unit.forEach((n) => nf1.appendChild(n.cloneNode(true)));
            unit.forEach((n) => nf2.appendChild(n.cloneNode(true)));
            track.appendChild(nf1);
            track.appendChild(nf2);
            offset = cur;
            track.style.transform = `translate3d(${-(offset % unitWidth)}px,0,0)`;
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
