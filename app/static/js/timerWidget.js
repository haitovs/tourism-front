// static/js/timerWidget.js
(function () {
    window.timerWidget = function ({ apiBase, bgUrl, logoUrl }) {
        return {
            apiBase,
            bgUrl,
            logoUrl,

            eventName: "",
            mode: "UNTIL_START",
            targetISO: null,
            serverISO: null,
            deltaMs: 0,

            dd: "00",
            hh: "00",
            mm: "00",
            ss: "00",
            _tickHandle: null,

            async init() {
                await this.fetchTimer();
                this.openWS();
                this.startTicking();
            },

            wsUrlFromBase() {
                try {
                    const u = new URL(this.apiBase);
                    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
                    u.pathname = "/ws/timer";
                    u.search = "";
                    return u.toString();
                } catch (e) {
                    const loc = window.location;
                    return (loc.protocol === "https:" ? "wss://" : "ws://") + loc.host + "/ws/timer";
                }
            },

            async fetchTimer() {
                const url = this.apiBase.replace(/\/+$/, "") + "/timer/active";
                try {
                    const res = await fetch(url, { credentials: "include" });
                    if (!res.ok) {
                        console.warn("[timer] fetch failed:", res.status, res.statusText);
                        setTimeout(() => this.fetchTimer(), 10000);
                        return;
                    }
                    const data = await res.json().catch((e) => {
                        console.error("[timer] bad JSON:", e);
                        return null;
                    });
                    if (!data) return;

                    this.eventName = data.event_name || "";
                    this.mode = data.mode || "UNTIL_START";
                    this.serverISO = data.server_time || null;
                    this.targetISO = (this.mode === "UNTIL_END" ? data.end_time : data.start_time) || null;

                    if (this.serverISO) {
                        const serverMs = Date.parse(this.serverISO);
                        this.deltaMs = Date.now() - serverMs;
                    } else {
                        this.deltaMs = 0;
                    }

                    if (!this.targetISO) console.warn("[timer] no target time in response");
                } catch (err) {
                    console.error("[timer] fetch error:", err);
                    setTimeout(() => this.fetchTimer(), 10000);
                }
            },

            openWS() {
                const wsURL = this.wsUrlFromBase();
                let ws;
                try {
                    ws = new WebSocket(wsURL);
                } catch (e) {
                    return;
                }
                ws.onmessage = (ev) => {
                    try {
                        const msg = JSON.parse(ev.data);
                        if (msg && msg.event === "TIMER_CREATED" && msg.data) {
                            const d = msg.data;
                            this.eventName = d.event_name || "";
                            this.mode = d.mode || "UNTIL_START";
                            this.targetISO = (this.mode === "UNTIL_END" ? d.end_time : d.start_time) || null;
                            this.deltaMs = 0;
                        }
                    } catch {}
                };
                ws.onerror = () => {};
                ws.onclose = () => {};
            },

            startTicking() {
                const update = () => {
                    if (!this.targetISO) {
                        this.dd = this.hh = this.mm = this.ss = "00";
                        this._tickHandle = setTimeout(update, 1000);
                        return;
                    }
                    const nowMs = Date.now() - this.deltaMs;
                    const targetMs = Date.parse(this.targetISO);
                    let remain = targetMs - nowMs;

                    if (isNaN(targetMs) || remain <= 0) {
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
