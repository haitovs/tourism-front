// static/js/timerWidget.js
(function () {
    const MONTHS_UPPER = [
        "JANUARY",
        "FEBRUARY",
        "MARCH",
        "APRIL",
        "MAY",
        "JUNE",
        "JULY",
        "AUGUST",
        "SEPTEMBER",
        "OCTOBER",
        "NOVEMBER",
        "DECEMBER",
    ];
    const safeParseISO = (iso) => {
        const ms = Date.parse(iso);
        return Number.isNaN(ms) ? null : ms;
    };

    function partsFromISO(iso) {
        const ms = safeParseISO(iso);
        if (!ms) return { day: "00", monthUpper: "" };
        const d = new Date(ms);
        const day = String(d.getUTCDate()).padStart(2, "0");
        const monthUpper = MONTHS_UPPER[d.getUTCMonth()] || "";
        return { day, monthUpper };
    }

    window.timerWidget = function ({ apiBase, bgUrl, logoUrl, site = null, siteId = null }) {
        return {
            apiBase,
            bgUrl,
            logoUrl,
            site,
            siteId,

            isDesktop: window.matchMedia("(min-width: 1024px)").matches,
            _mq: null,
            _ws: null,
            _tickHandle: null,

            eventName: "",
            mode: "UNTIL_START",
            targetISO: null,
            serverISO: null,
            deltaMs: 0,

            dd: "00",
            hh: "00",
            mm: "00",
            ss: "00",
            deadlineDay: "00",
            deadlineMonthUpper: "",

            async init() {
                // media query listener
                this._mq = window.matchMedia("(min-width: 1024px)");
                const mqHandler = (e) => (this.isDesktop = e.matches);
                if (this._mq.addEventListener) this._mq.addEventListener("change", mqHandler);
                else this._mq.addListener(mqHandler);
                window.addEventListener("beforeunload", () => {
                    if (this._ws && this._ws.readyState === 1) this._ws.close();
                    if (this._mq && this._mq.removeEventListener) this._mq.removeEventListener("change", mqHandler);
                });

                // optional auto-site via meta if nothing passed
                if (this.siteId == null && !this.site) {
                    const m = document.querySelector('meta[name="site-slug"]');
                    if (m && m.content) this.site = m.content.trim();
                }

                await this.fetchTimer();
                this.openWS();
                this.startTicking();
            },

            wsUrlFromBase() {
                const loc = window.location;
                const pageIsSecure = loc.protocol === "https:";
                const makeUrl = (base) => {
                    const u = new URL(base, loc.origin);
                    // Don't replace the backend URL - use it as-is
                    const secure = pageIsSecure || u.protocol === "https:";
                    u.protocol = secure ? "wss:" : "ws:";
                    u.pathname = "/ws/timer";
                    u.search = "";
                    return u.toString();
                };
                try {
                    return makeUrl(this.apiBase || loc.origin);
                } catch {
                    return (pageIsSecure ? "wss://" : "ws://") + loc.host + "/ws/timer";
                }
            },

            _applyPayload(data) {
                this.eventName = data.event_name || this.eventName || "";
                this.mode = data.mode || this.mode || "UNTIL_START";
                this.serverISO = data.server_time || null;

                const iso = (this.mode === "UNTIL_END" ? data.end_time : data.start_time) || null;
                this.targetISO = iso;
                this.deltaMs = this.serverISO ? Date.now() - Date.parse(this.serverISO) : 0;

                if (iso) {
                    const { day, monthUpper } = partsFromISO(iso);
                    this.deadlineDay = day;
                    this.deadlineMonthUpper = monthUpper;
                } else {
                    this.deadlineDay = "00";
                    this.deadlineMonthUpper = "";
                }
            },

            async fetchTimer() {
                const base = (this.apiBase || "").replace(/\/+$/, "");
                const here = window.location.origin.replace(/\/+$/, "");
                const qs = new URLSearchParams();
                if (this.siteId != null) qs.set("site_id", String(this.siteId));
                else if (this.site) qs.set("site", this.site);
                const suffix = qs.toString() ? `?${qs.toString()}` : "";
                const headers = this.site ? { "X-Site-Slug": this.site } : undefined;

                // Try FRONT first, then FRONT fallback (/api/timer), then BACKEND last
                const candidates = [
                    `${here}/timer/active${suffix}`, // front proxy (site-aware if your front router injects)
                    `${here}/api/timer`, // front fallback (settings-based deadline)
                    base ? `${base}/timer/active${suffix}` : null, // backend last
                ].filter(Boolean);

                let lastErr;
                for (const url of candidates) {
                    try {
                        const res = await fetch(url, { credentials: "include", headers });
                        if (!res.ok) {
                            lastErr = res.status + " " + res.statusText;
                            continue;
                        }
                        const j = await res.json().catch(() => null);
                        if (!j) {
                            lastErr = "invalid json";
                            continue;
                        }

                        // unify /api/timer fallback payload to backend shape
                        if ("deadline_iso_utc" in j) {
                            const unified = {
                                event_name: j.event_name || "",
                                mode: "UNTIL_END",
                                start_time: null,
                                end_time: j.deadline_iso_utc,
                                server_time: new Date().toISOString(),
                            };
                            this._applyPayload(unified);
                            return;
                        }

                        // backend/forwarded payload
                        this._applyPayload(j);
                        return;
                    } catch (e) {
                        lastErr = String(e);
                    }
                }
                console.warn("[timer] active fetch failed:", lastErr);
                setTimeout(() => this.fetchTimer(), 10000);
            },

            openWS() {
                let ws;
                try {
                    ws = new WebSocket(this.wsUrlFromBase());
                } catch {
                    return;
                }
                this._ws = ws;

                const acceptForThisPage = (d) => {
                    if (this.siteId != null && d.site_id !== this.siteId) return false;
                    if (this.site && d.site && this.site !== d.site) return false;
                    if (this.siteId == null && !this.site && d.site_id != null) return false; // default page: ignore site-scoped pushes
                    return true;
                };

                ws.onmessage = (ev) => {
                    try {
                        const msg = JSON.parse(ev.data);
                        if (!msg || !msg.data) return;
                        if (
                            (msg.event === "TIMER_CREATED" || msg.event === "TIMER_UPDATE") &&
                            acceptForThisPage(msg.data)
                        ) {
                            this._applyPayload(msg.data);
                        }
                    } catch {}
                };
                ws.onerror = () => {};
                ws.onclose = () => {
                    this._ws = null;
                };
            },

            startTicking() {
                const update = () => {
                    if (!this.targetISO) {
                        this.dd = this.hh = this.mm = this.ss = "00";
                        this._tickHandle = setTimeout(update, 1000);
                        return;
                    }
                    const targetMs = safeParseISO(this.targetISO);
                    const nowMs = Date.now() - this.deltaMs;
                    const remain = (targetMs ?? 0) - nowMs;

                    if (!targetMs || remain <= 0) {
                        this.dd = this.hh = this.mm = this.ss = "00";
                        this._tickHandle = setTimeout(update, 1000);
                        return;
                    }
                    const sec = Math.floor(remain / 1000);
                    const days = Math.floor(sec / 86400);
                    const hrs = Math.floor((sec % 86400) / 3600);
                    const mins = Math.floor((sec % 3600) / 60);
                    const secs = sec % 60;

                    this.dd = String(days).padStart(2, "0");
                    this.hh = String(hrs).padStart(2, "0");
                    this.mm = String(mins).padStart(2, "0");
                    this.ss = String(secs).padStart(2, "0");

                    this._tickHandle = setTimeout(update, 1000);
                };
                update();
            },
        };
    };
})();
