import html
import zipfile
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import quote

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.core.templates import templates, themed_name

router = APIRouter()

_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _extract_docx_html(path: Path) -> str:
    """
    Minimal DOCX -> HTML: pull paragraph text, keep basic line breaks.
    We keep only text runs to avoid heavy dependencies.
    """
    if not path.exists():
        return ""

    # Prefer mammoth if the user installs it (much richer HTML output)
    try:
        import mammoth  # type: ignore

        with path.open("rb") as f:
            res = mammoth.convert_to_html(f)
        if res and res.value:
            return res.value
    except Exception:
        pass

    if not path.exists():
        return ""
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
    except Exception:
        return ""

    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml)
    except Exception:
        return ""

    paragraphs = []

    def _collect_text(el):
        out = []
        for node in el.iter():
            tag = node.tag
            if tag.endswith("}t"):
                if node.text:
                    out.append(node.text)
            elif tag.endswith("}tab"):
                out.append("\t")
            elif tag.endswith("}br"):
                out.append("\n")
        return "".join(out).strip()

    body = root.find(f".//{_W_NS}body")
    if body is None:
        return ""
    for p in body.findall(f"{_W_NS}p"):
        txt = _collect_text(p)
        if txt:
            paragraphs.append(f"<p>{html.escape(txt)}</p>")

    return "\n".join(paragraphs)


def _resolve_doc_path(req: Request, exts: Iterable[str] = (".png", ".jpg", ".jpeg", ".pdf", ".docx")) -> Optional[Path]:
    """
    Pick the document file based on site slug and lang.
    - docs/{slug}/*-en.{ext} or *-ru.{ext}
    - default language en; ru prefers ru if exists, otherwise en
    - fallback to first available file in docs/* if slug missing
    """
    lang = getattr(req.state, "lang", "en") or "en"
    slug = getattr(getattr(req.state, "site", None), "slug", None) or "turkmenchina"

    base = Path(__file__).parent.parent / "static" / "docs"
    preferred_langs = ["ru", "en"] if lang.startswith("ru") else ["en", "ru"]
    exts = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts]

    def pick_in_folder(folder: Path) -> Optional[Path]:
        if not folder.exists() or not folder.is_dir():
            return None
        for lng in preferred_langs:
            for ext in exts:
                matches = sorted(folder.glob(f"*{lng}{ext}"))
                if matches:
                    return matches[0]
        return None

    # try current site folder first
    choice = pick_in_folder(base / slug)
    if choice:
        return choice

    # fallback: first matching file in any folder
    if base.exists():
        for folder in base.iterdir():
            if not folder.is_dir():
                continue
            choice = pick_in_folder(folder)
            if choice:
                return choice
    # ultimate fallback: first file in tree
    for ext in exts:
        for f in base.rglob(f"*{ext}"):
            return f
    return None


@router.get("/official-support", response_class=HTMLResponse)
async def official_support_page(request: Request):
    template_name = themed_name(request, "official_support.html")
    doc_path = _resolve_doc_path(request)
    suffix = doc_path.suffix.lower() if doc_path else ""
    doc_is_pdf = suffix == ".pdf"
    doc_is_image = suffix in {".png", ".jpg", ".jpeg"}
    doc_html = _extract_docx_html(doc_path) if (doc_path and not doc_is_pdf and not doc_is_image) else ""

    doc_url = ""  # relative
    doc_url_abs = ""
    viewer_url = ""
    viewer_url_alt = ""
    doc_embed_url = ""
    doc_image_url = ""
    if doc_path:
        static_root = Path(__file__).parent.parent / "static"
        try:
            try:
                rel_to_static = doc_path.relative_to(static_root).as_posix()
            except Exception:
                parts = doc_path.as_posix().split("/static/", 1)
                rel_to_static = parts[1] if len(parts) == 2 else ""
            if rel_to_static:
                # relative and absolute URLs
                doc_url = f"/static/{rel_to_static}"
                doc_url_abs = f"{request.base_url}static/{rel_to_static}"
                try:
                    doc_url_abs = str(request.url_for("static", path=rel_to_static))
                except Exception:
                    pass
                doc_embed_url = doc_url_abs or doc_url
                if doc_is_image:
                    doc_image_url = doc_embed_url
                else:
                    viewer_url = f"https://docs.google.com/gview?embedded=1&url={quote(doc_url_abs, safe='')}"
                    viewer_url_alt = f"https://view.officeapps.live.com/op/embed.aspx?src={quote(doc_url_abs, safe='')}"
        except Exception:
            doc_url = ""
            doc_url_abs = ""
            viewer_url = ""
            viewer_url_alt = ""
            doc_embed_url = ""
            doc_image_url = ""

    # If we already have parsed HTML (mammoth or fallback), skip external viewers.
    if doc_html:
        viewer_url = ""
        viewer_url_alt = ""
    # If it's a PDF, prefer the browser's built-in viewer via direct embed URL.
    if doc_is_pdf and doc_embed_url:
        viewer_url = doc_embed_url
        viewer_url_alt = ""
    # If it's an image, use the image URL.
    if doc_is_image and doc_image_url:
        viewer_url = ""
        viewer_url_alt = ""

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "doc_html": doc_html,
            "doc_filename": doc_path.name if doc_path else "",
            "doc_url": doc_url,
            "doc_url_abs": doc_url_abs,
            "viewer_url": viewer_url,
            "viewer_url_alt": viewer_url_alt,
            "doc_is_pdf": doc_is_pdf,
            "doc_embed_url": doc_embed_url,
            "doc_is_image": doc_is_image,
            "doc_image_url": doc_image_url,
        },
    )
