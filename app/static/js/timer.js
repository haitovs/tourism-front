// static/js/timer.js
(function () {
    const pad2 = (n) => String(Math.max(0, n)).padStart(2, "0");

    function splitDiff(ms) {
        if (ms <= 0) return { d: 0, h: 0, m: 0 };
        const s = Math.floor(ms / 1000);
        const d = Math.floor(s / 86400);
        const h = Math.floor((s % 86400) / 3600);
        const m = Math.floor((s % 3600) / 60);
        return { d, h, m };
    }

    async function fetchDeadlineISO() {
        try {
            const res = await fetch("/api/timer", { credentials: "same-origin" });
            if (!res.ok) throw new Error("timer api failed");
            const j = await res.json();
            return j?.deadline_iso_utc || null;
        } catch (e) {
            console.error(e);
            return null;
        }
    }

    function startTimer(root, isoUTC) {
        const daysEl = root.querySelector("[data-days]");
        const hoursEl = root.querySelector("[data-hours]");
        const minsEl = root.querySelector("[data-mins]");
        const stateEl = root.querySelector("[data-state]");

        const targetMs = Date.parse(isoUTC);
        if (Number.isNaN(targetMs)) {
            console.error("Invalid deadline ISO:", isoUTC);
            return;
        }

        function render() {
            const diff = targetMs - Date.now();
            if (diff <= 0) {
                if (stateEl) stateEl.textContent = "Expired";
                if (daysEl) daysEl.textContent = "00";
                if (hoursEl) hoursEl.textContent = "00";
                if (minsEl) minsEl.textContent = "00";
                return true; // stop
            }

            const { d, h, m } = splitDiff(diff);
            if (stateEl) stateEl.textContent = "The remaining";
            if (daysEl) daysEl.textContent = pad2(d);
            if (hoursEl) hoursEl.textContent = pad2(h);
            if (minsEl) minsEl.textContent = pad2(m);
            return false;
        }

        if (render()) return;
        const id = setInterval(() => render() && clearInterval(id), 1000);
    }

    window.addEventListener("DOMContentLoaded", async () => {
        const nodes = document.querySelectorAll("[data-countdown]");
        if (!nodes.length) return;

        for (const root of nodes) {
            let iso = root.getAttribute("data-deadline");
            if (!iso) iso = await fetchDeadlineISO(); // fallback to API
            if (iso) startTimer(root, iso);
            else console.warn("No deadline available for countdown.");
        }
    });
})();
