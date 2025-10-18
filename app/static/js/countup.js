// static/js/countup.js
(function () {
    function makeCountup({ values, duration = 1500 }) {
        return {
            target: values || {},
            display: { episodes: 0, delegates: 0, speakers: 0, companies: 0 },
            started: false,
            start() {
                if (this.started) return;
                this.started = true;

                const keys = Object.keys(this.target);
                const startTime = performance.now();

                const tick = (now) => {
                    const t = Math.min(1, (now - startTime) / duration);
                    const e = 1 - Math.pow(1 - t, 3); // easeOutCubic
                    keys.forEach((k) => (this.display[k] = Math.floor(e * (this.target[k] || 0))));
                    if (t < 1) requestAnimationFrame(tick);
                    else keys.forEach((k) => (this.display[k] = this.target[k] || 0));
                };

                requestAnimationFrame(tick);
            },
        };
    }

    // Keep the old global factory (in case you still call window.countup from elsewhere)
    window.countup = makeCountup;

    // Register as an Alpine component (rock-solid init)
    document.addEventListener("alpine:init", () => {
        window.Alpine.data("countup", (opts) => makeCountup(opts || {}));
    });
})();
