# app/routers/site.py
import logging
from asyncio import create_task, gather

from fastapi import APIRouter, Request, Response
from starlette.responses import HTMLResponse, RedirectResponse

from app.core.language_middleware import LANG_COOKIE
from app.services import expo_sectors as sectors_srv
from app.services import faqs as faq_srv
from app.services import news as news_srv
from app.services import organizers as org_srv
from app.services import participants as participants_srv
from app.services import partners as partners_srv
from app.services import speakers as speakers_srv
from app.services import sponsors as sponsor_srv
from app.services import statistics as stats_srv
from app.services import timer as timer_srv

from ..core.settings import settings
from ..core.templates import templates

router = APIRouter()


def _resolve_site_id(req: Request) -> int | None:
    site = getattr(req.state, "site", None)
    return getattr(site, "id", None) if site else None


def _resolve_home_limits(req: Request) -> dict:
    """
    Returns per-site limits for home widgets.
    - Site-aware defaults via site.slug (or site.name lowercased)
    - URL override: ?limit.sectors=6 (and similar)
    """
    q = req.query_params or {}

    def _qint(key: str, default: int) -> int:
        qkey = f"limit.{key}"
        if qkey in q:
            try:
                v = int(q[qkey])
                return max(0, v)
            except Exception:
                return default
        return default

    site = getattr(req.state, "site", None)
    slug = (getattr(site, "slug", None) or getattr(site, "name", None) or "").lower()

    # Defaults for the “default” site
    limits = {
        "sectors_fetch": 3,
        "sectors_display": 6,
        "speakers": 3,
        "news": 5,
        "faqs": 5,
        "participants_all": 200,
        "participants_home": 12,
        "participants_expo": 8,
        "participants_forum": 8,
        "participants_both": 8,
    }

    # Site-specific overrides
    overrides = {
        "site-b": {
            "sectors_fetch": 12,  # grab more; we’ll display 6
            "sectors_display": 6,
        },
        # add more sites here...
    }

    limits.update(overrides.get(slug, {}))

    for k in list(limits.keys()):
        limits[k] = _qint(k, limits[k])

    for k, v in list(limits.items()):
        if v is None or v < 0:
            limits[k] = 0

    return limits


@router.post("/set-lang/{code}")
def set_lang(code: str, request: Request, response: Response):
    code = (code or "").lower().split("-")[0]
    if code not in settings.SUPPORTED_LANGS:
        code = settings.DEFAULT_LANG
    response.set_cookie(LANG_COOKIE, code, max_age=60 * 60 * 24 * 365, samesite="lax")
    referer = request.headers.get("referer") or "/"
    return RedirectResponse(referer, status_code=303)


@router.get("/", response_class=HTMLResponse)
async def home(req: Request):
    log = logging.getLogger("routers.site.home")

    lang = getattr(req.state, "lang", settings.DEFAULT_LANG)
    site_id = _resolve_site_id(req)
    limits = _resolve_home_limits(req)

    # timer (sync)
    deadline_dt = timer_srv.get_deadline_from_settings(settings)
    timer_ctx = timer_srv.build_timer_context(deadline_dt)

    sponsors_bundle_task = create_task(
        sponsor_srv.get_homepage_bundle(lang=lang, site_id=site_id, max_top_items=5)
    )
    stats_task = create_task(stats_srv.get_statistics(site_id=site_id))

    # async fetches — use site-aware limits
    sectors_task = create_task(sectors_srv.list_home_sectors(req, limit=limits["sectors_fetch"], latest_first=True))
    news_task = create_task(news_srv.get_latest_news(req, limit=limits["news"]))
    faqs_task = create_task(faq_srv.list_faqs(req, limit=limits["faqs"]))
    speakers_task = create_task(speakers_srv.get_featured_speakers(req, limit=limits["speakers"]))
    organizers_task = create_task(org_srv.list_organizers(req, limit=None))
    partners_task = create_task(partners_srv.list_partners(req, limit=None))
    participants_all_task = create_task(participants_srv.list_participants(req, limit=limits["participants_all"], latest_first=True))

    results = await gather(
        sectors_task,
        news_task,
        faqs_task,
        speakers_task,
        organizers_task,
        partners_task,
        participants_all_task,
        return_exceptions=True,
    )

    def _ok(idx):
        val = results[idx]
        if isinstance(val, Exception):
            log.warning("home(): task %d failed: %r", idx, val)
            return []
        return val or []

    sectors = _ok(0)
    news = _ok(1)
    faqs = _ok(2)
    speakers = _ok(3)
    organizers = _ok(4)
    partners = _ok(5)
    participants_all = _ok(6)

    # Derive participant slices with limits
    participants = participants_all[:limits["participants_home"]]
    participants_expo = [p for p in participants_all if (p.get("role") in {"expo", "both"})][:limits["participants_expo"]]
    participants_forum = [p for p in participants_all if (p.get("role") in {"forum", "both"})][:limits["participants_forum"]]
    participants_both = [p for p in participants_all if p.get("role") == "both"][:limits["participants_both"]]

    def _empty_top():
        return {t: [] for t in ("premier", "general", "diamond", "platinum")}

    try:
        sponsors_bundle = await sponsors_bundle_task
    except Exception as exc:
        log.warning("home(): sponsors bundle failed: %r", exc)
        sponsors_bundle = {
            "sponsors_top": _empty_top(),
            "sponsors_top_flat": {"items": [], "count": 0},
            "sponsors_top_view": {"items": [], "count": 0, "layout": "empty", "max": 5},
            "gold": {"items": [], "tier": "gold", "count": 0, "layout": "empty", "rows": [], "marquee_rows": []},
            "silver": {"items": [], "tier": "silver", "count": 0, "layout": "empty", "rows": [], "marquee_rows": []},
            "bronze": {"items": [], "tier": "bronze", "count": 0, "layout": "empty", "rows": [], "marquee_rows": []},
        }

    try:
        stats = await stats_task
    except Exception as exc:
        log.warning("home(): statistics failed: %r", exc)
        stats = {"episodes": 0, "delegates": 0, "speakers": 0, "companies": 0}

    ctx = {
        "request": req,
        "lang": lang,
        "settings": settings,

        # sponsors/statistics
        "sponsors_top": sponsors_bundle.get("sponsors_top", _empty_top()),
        "sponsors_top_flat": sponsors_bundle.get("sponsors_top_flat", {"items": [], "count": 0}),
        "sponsors_top_view": sponsors_bundle.get("sponsors_top_view", {"items": [], "count": 0, "layout": "empty"}),
        "gold": sponsors_bundle.get("gold", {"items": [], "tier": "gold", "count": 0, "layout": "empty"}),
        "silver": sponsors_bundle.get("silver", {"items": [], "tier": "silver", "count": 0, "layout": "empty"}),
        "bronze": sponsors_bundle.get("bronze", {"items": [], "tier": "bronze", "count": 0, "layout": "empty"}),
        "stats": stats,

        # async results (flat + {items:[…]} for theme compatibility)
        "sectors": sectors,
        "sectors_data": {
            "items": sectors
        },
        "news": news,
        "news_data": {
            "items": news
        },
        "faqs": faqs,
        "faqs_data": {
            "items": faqs
        },
        "speakers": speakers,
        "speakers_data": {
            "items": speakers
        },

        # organizers / partners (flat + items)
        "organizers": organizers,
        "organizers_data": {
            "items": organizers
        },
        "partners": partners,
        "partners_data": {
            "items": partners
        },

        # participants (derived locally)
        "participants": participants,
        "participants_expo": participants_expo,
        "participants_forum": participants_forum,
        "participants_both": participants_both,

        # limits exposed to templates (e.g., sectors slice)
        "limits": limits,

        # timer
        "timer": timer_ctx,
    }

    return templates.TemplateResponse("index.html", ctx)
