// static/js/participantLoader.js
(() => {
    function escapeHtml(str) {
        return String(str || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function cardHTML(p) {
        // Detect theme by checking if we're on site-b based on body class or other indicator
        const isSiteB = document.body.classList.contains('site-b') ||
            document.querySelector('.sb-page-hero') !== null;

        // Theme-specific colors
        const primaryColor = isSiteB ? '#20306C' : '#007A3D';
        const badgeBg = isSiteB ? '#DCE3FF' : '#D3F2E2';

        const role = (p.role || "").toString();
        const roleChip = role
            ? `<span class="shrink-0 inline-flex items-center px-2.5 h-7 rounded-md bg-[${badgeBg}] text-[${primaryColor}] font-['Roboto'] text-sm font-medium">${escapeHtml(
                role.charAt(0).toUpperCase() + role.slice(1)
            )}</span>`
            : "";
        const logo = p.logo_url || "/static/img/default_participant.png";
        const safeName = escapeHtml(p.name || "");
        const id = String(p.id || "").replace(/[^0-9a-zA-Z_-]/g, "");

        return `
      <a href="/participants/${id}"
         aria-label="${safeName}"
         class="group block bg-white rounded-[15px] shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-[${primaryColor}] transition overflow-hidden">
        <div class="h-[200px] w-full bg-slate-50">
          <img src="${logo}" alt="${safeName}" class="w-full h-full object-contain p-4" />
        </div>
        <div class="p-5">
          <div class="flex items-start justify-between gap-3">
            <h3 class="font-['Roboto'] font-medium text-[22px] leading-7 text-[#1E1E1E] transition-colors group-hover:text-[${primaryColor}]">
              ${safeName}
            </h3>
            ${roleChip}
          </div>
        </div>
      </a>
    `.trim();
    }

    function initParticipantLoader() {
        const grid = document.getElementById("participants-grid");
        if (!grid) return;

        const btn = document.getElementById("load-more-btn");
        const sentinel = document.getElementById("infinite-sentinel");

        const limit = Number(grid.dataset.limit || 12);
        let offset = Number(grid.dataset.offset || 0);
        const role = grid.dataset.role || "";
        const q = grid.dataset.q || "";
        let loading = false;
        let done = false;
        let controller = null;

        async function loadMore() {
            if (loading || done) return;
            loading = true;
            grid.setAttribute("aria-busy", "true");

            if (controller) controller.abort();
            controller = new AbortController();

            const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
            if (role) params.set("role", role);
            if (q) params.set("q", q);

            try {
                const res = await fetch(`/api/participants?${params.toString()}`, { signal: controller.signal });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();

                const items = Array.isArray(data.items) ? data.items : [];
                if (items.length > 0) {
                    const frag = document.createDocumentFragment();
                    for (const p of items) {
                        const wrapper = document.createElement("div");
                        wrapper.innerHTML = cardHTML(p);
                        frag.appendChild(wrapper.firstElementChild);
                    }
                    grid.appendChild(frag);
                }

                if (data.next_offset == null) {
                    done = true;
                    if (observer) observer.disconnect();
                    if (btn) btn.style.display = "none";
                    if (sentinel) sentinel.remove();
                } else {
                    offset = Number(data.next_offset);
                    if (btn) btn.style.display = "inline-flex"; // keep fallback visible
                }
            } catch (e) {
                // Show fallback button so user can retry manually
                if (btn) btn.style.display = "inline-flex";
                console.error("[participants] loadMore error:", e);
            } finally {
                loading = false;
                grid.setAttribute("aria-busy", "false");
            }
        }

        const observer =
            "IntersectionObserver" in window
                ? new IntersectionObserver(
                    (entries) => entries.forEach((entry) => entry.isIntersecting && loadMore()),
                    { rootMargin: "600px 0px 600px 0px" }
                )
                : null;

        if (observer && sentinel) observer.observe(sentinel);
        if (btn) btn.addEventListener("click", () => loadMore());
    }

    // Auto-init when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initParticipantLoader);
    } else {
        initParticipantLoader();
    }

    // Optional: expose for manual re-init (e.g., after PJAX/nav)
    window.initParticipantLoader = initParticipantLoader;
})();
