"""Local vector illustrations.

The text model drafts an SVG; this module extracts it and rebuilds a *safe* document
from a strict whitelist of elements and attributes. Nothing the model writes is ever
passed through verbatim, so scripts, external references and styles cannot get in.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
MAX_ELEMENTS = 500
MAX_PATH_CHARS = 6000
MAX_TEXT_CHARS = 140
MIN_DRAWN_ELEMENTS = 8

ALLOWED_TAGS = {
    "svg", "g", "defs", "linearGradient", "radialGradient", "stop", "rect", "circle", "ellipse",
    "line", "polyline", "polygon", "path", "text", "tspan",
}
DRAWN_TAGS = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text"}
ALLOWED_ATTRS = {
    "id", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "d", "points",
    "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-dasharray",
    "opacity", "fill-opacity", "stroke-opacity", "transform", "offset", "stop-color", "stop-opacity",
    "gradientUnits", "gradientTransform", "fx", "fy", "font-size", "font-weight", "font-family",
    "text-anchor", "dominant-baseline", "fill-rule", "clip-rule",
}
_PATH_CHARS = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+\-]*$")
_TRANSFORM = re.compile(r"^(?:\s*(?:translate|rotate|scale|skewX|skewY|matrix)\s*\([0-9eE.,\s+\-]*\)\s*)*$")
_NUMERIC_LIST = re.compile(r"^[0-9eE.,\s+\-%]*$")
_PAINT = re.compile(r"^(?:none|currentColor|transparent|#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,24}|"
                    r"(?:rgb|rgba|hsl|hsla)\([0-9.,%\s]+\)|url\(#[A-Za-z0-9_-]{1,40}\))$")
_SAFE_FONT = re.compile(r"^[A-Za-z0-9 ,'\"_-]{1,80}$")
_COLOR_ATTRS = {"fill", "stroke", "stop-color"}
_NUMBER_ATTRS = {"x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "fx", "fy",
                 "stroke-width", "opacity", "fill-opacity", "stroke-opacity", "stop-opacity", "offset",
                 "font-size", "font-weight", "stroke-dasharray"}


class SvgRejected(ValueError):
    pass


SVG_EXAMPLE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">'
    '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff9a5a"/>'
    '<stop offset="1" stop-color="#ffd9a0"/></linearGradient>'
    '<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a6f9e"/>'
    '<stop offset="1" stop-color="#123c5c"/></linearGradient>'
    '<radialGradient id="sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fffbe0"/>'
    '<stop offset="1" stop-color="#ffcf6b"/></radialGradient></defs>'
    '<rect width="1024" height="1024" fill="url(#sky)"/>'
    '<circle cx="512" cy="590" r="210" fill="#ffe9b0" opacity="0.35"/>'
    '<circle cx="512" cy="590" r="140" fill="url(#sun)"/>'
    '<path d="M0 560 L180 470 L330 560 Z" fill="#8c5a5a" opacity="0.7"/>'
    '<path d="M640 560 L820 450 L1024 560 Z" fill="#7a4d57" opacity="0.7"/>'
    '<rect y="600" width="1024" height="424" fill="url(#sea)"/>'
    '<ellipse cx="512" cy="660" rx="150" ry="14" fill="#ffe7a8" opacity="0.7"/>'
    '<ellipse cx="512" cy="700" rx="110" ry="10" fill="#ffe7a8" opacity="0.5"/>'
    '<ellipse cx="512" cy="745" rx="70" ry="8" fill="#ffe7a8" opacity="0.4"/>'
    '<path d="M0 640 Q128 620 256 640 T512 640 T768 640 T1024 640" fill="none" stroke="#ffffff" stroke-width="4" opacity="0.45"/>'
    '<path d="M0 820 Q128 800 256 820 T512 820 T768 820 T1024 820" fill="none" stroke="#ffffff" stroke-width="5" opacity="0.3"/>'
    '<path d="M150 200 q20 -20 40 0 q20 -20 40 0" fill="none" stroke="#5b3a3a" stroke-width="5" stroke-linecap="round"/>'
    '<path d="M780 260 q16 -16 32 0 q16 -16 32 0" fill="none" stroke="#5b3a3a" stroke-width="4" stroke-linecap="round"/>'
    '<polygon points="60,1024 140,880 220,1024" fill="#0d2a40"/>'
    '</svg>'
)


def build_svg_prompt(subject: str, width: int, height: int) -> str:
    return (
        f"Sei un illustratore vettoriale professionista. Disegna in SVG: {subject}\n\n"
        f"Tela: viewBox=\"0 0 {width} {height}\". Rispondi SOLO con il codice SVG completo, da <svg> a </svg>, "
        "senza Markdown e senza spiegazioni.\n"
        "Regole:\n"
        "- Usa solo rect, circle, ellipse, line, polyline, polygon, path, g, defs, linearGradient, radialGradient, stop"
        " e text (solo se il testo è richiesto).\n"
        "- Sfondo a tutta tela con gradiente, poi piani sovrapposti (sfondo, soggetto, dettagli, primo piano).\n"
        "- Almeno 15 elementi, soggetto riconoscibile e centrato, palette armoniosa di 5-7 colori, ombre e luci con"
        " forme semitrasparenti.\n"
        "- Nessuno script, immagine esterna, filtro, stile CSS o font esterno. Chiudi tutti i tag.\n\n"
        f"Esempio di struttura e livello di dettaglio minimo (tramonto sul mare):\n{SVG_EXAMPLE}"
    )


def extract_svg(text: str) -> str:
    """Return the first complete <svg>...</svg> block found in a model reply."""
    if not isinstance(text, str):
        raise SvgRejected("Il modello non ha restituito testo.")
    start = text.find("<svg")
    end = text.rfind("</svg>")
    if start < 0:
        raise SvgRejected("Il modello non ha prodotto un disegno SVG.")
    if end < start:
        # Truncated reply: close the document so the drawn part can still be validated.
        body = text[start:]
        last_close = max(body.rfind("/>"), body.rfind(">"))
        return body[: last_close + 1] + "</svg>" if last_close > 0 else ""
    return text[start:end + len("</svg>")]


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _clean_value(name: str, value: str) -> str | None:
    value = value.strip()
    if not value or len(value) > MAX_PATH_CHARS:
        return None
    low = value.lower()
    if "javascript:" in low or "data:" in low or "<" in value or "&" in value or "@import" in low:
        return None
    if name == "d":
        return value if _PATH_CHARS.match(value) else None
    if name in {"points", "stroke-dasharray"}:
        return value if _NUMERIC_LIST.match(value) else None
    if name in {"transform", "gradientTransform"}:
        return value if _TRANSFORM.match(value) else None
    if name in _COLOR_ATTRS:
        return value if _PAINT.match(value) else None
    if name == "font-family":
        return value if _SAFE_FONT.match(value) else None
    if name in _NUMBER_ATTRS:
        return value if _NUMERIC_LIST.match(value) else None
    if name == "id":
        return value if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,39}", value) else None
    if name in {"gradientUnits"}:
        return value if value in {"userSpaceOnUse", "objectBoundingBox"} else None
    if name in {"stroke-linecap", "stroke-linejoin", "text-anchor", "dominant-baseline", "fill-rule", "clip-rule"}:
        return value if re.fullmatch(r"[a-z-]{3,24}", value) else None
    return value if re.fullmatch(r"[A-Za-z0-9 .,#%()_-]{1,60}", value) else None


def _rebuild(source: ET.Element, parent: ET.Element | None, counter: list[int], ids: set[str]) -> ET.Element | None:
    tag = _local(source.tag)
    if tag not in ALLOWED_TAGS:
        return None
    counter[0] += 1
    if counter[0] > MAX_ELEMENTS:
        raise SvgRejected("Il disegno contiene troppi elementi.")
    node = ET.Element(f"{{{SVG_NS}}}{tag}") if parent is None else ET.SubElement(parent, f"{{{SVG_NS}}}{tag}")
    for raw_name, raw_value in source.attrib.items():
        name = _local(raw_name)
        if name not in ALLOWED_ATTRS or tag == "svg":
            continue
        cleaned = _clean_value(name, raw_value)
        if cleaned is not None:
            node.set(name, cleaned)
            if name == "id":
                ids.add(cleaned)
    if tag in {"text", "tspan"} and source.text:
        node.text = " ".join(source.text.split())[:MAX_TEXT_CHARS]
    for child in list(source):
        built = _rebuild(child, node, counter, ids)
        if built is None:
            continue
        if tag in {"text", "tspan"} and child.tail and built is not None:
            built.tail = " ".join(child.tail.split())[:MAX_TEXT_CHARS]
    return node


def _viewbox(source: ET.Element, width: int, height: int) -> tuple[float, float]:
    raw = source.attrib.get("viewBox", "")
    try:
        parts = [float(item) for item in re.split(r"[\s,]+", raw.strip()) if item]
        if len(parts) == 4 and parts[0] == 0 and parts[1] == 0 and 16 <= parts[2] <= 4096 and 16 <= parts[3] <= 4096:
            return parts[2], parts[3]
    except ValueError:
        pass
    return float(width), float(height)


def sanitize_svg(svg_text: str, width: int = 1024, height: int = 1024) -> bytes:
    """Validate and rebuild an SVG from a whitelist. Raises SvgRejected on anything unusable."""
    if not svg_text or len(svg_text) > 400_000:
        raise SvgRejected("Disegno vuoto o troppo grande.")
    low = svg_text.lower()
    if "<!doctype" in low or "<!entity" in low or "<?xml-stylesheet" in low:
        raise SvgRejected("Il disegno contiene dichiarazioni non consentite.")
    # Models often write a bare "&" or an unquoted attribute; one tolerant clean-up pass.
    prepared = re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+);)", "&amp;", svg_text)
    if "xmlns=" not in prepared[:300]:
        prepared = prepared.replace("<svg", f'<svg xmlns="{SVG_NS}"', 1)
    try:
        root = ET.fromstring(prepared)
    except ET.ParseError as exc:
        raise SvgRejected("Il disegno prodotto non è un SVG valido.") from exc
    if _local(root.tag) != "svg":
        raise SvgRejected("Il documento non è un SVG.")
    vb_w, vb_h = _viewbox(root, width, height)
    counter = [0]
    ids: set[str] = set()
    ET.register_namespace("", SVG_NS)
    rebuilt = _rebuild(root, None, counter, ids)
    if rebuilt is None:
        raise SvgRejected("Disegno non utilizzabile.")
    rebuilt.set("viewBox", f"0 0 {vb_w:g} {vb_h:g}")
    rebuilt.set("width", str(int(vb_w)))
    rebuilt.set("height", str(int(vb_h)))
    rebuilt.set("role", "img")
    # Paint servers may only point to gradients that actually exist in this document.
    for element in rebuilt.iter():
        for name in ("fill", "stroke"):
            value = element.get(name, "")
            match = re.fullmatch(r"url\(#([A-Za-z0-9_-]+)\)", value)
            if match and match.group(1) not in ids:
                element.set(name, "#888888" if name == "fill" else "none")
    drawn = sum(1 for element in rebuilt.iter() if _local(element.tag) in DRAWN_TAGS)
    if drawn < MIN_DRAWN_ELEMENTS:
        raise SvgRejected("Il disegno è troppo scarno per essere utile.")
    data = ET.tostring(rebuilt, encoding="unicode")
    return ('<?xml version="1.0" encoding="UTF-8"?>' + data).encode("utf-8")


# ---------------------------------------------------------------------------
# Deterministic geometric figures: instant, exact, no model involved.
# ---------------------------------------------------------------------------
_SHAPE_WORDS = (
    ("cubo", "cube"), ("quadrato", "square"), ("rettangolo", "rectangle"), ("triangolo", "triangle"),
    ("cerchio", "circle"), ("piramide", "pyramid"), ("parallelepipedo", "box"),
)


def detect_geometric_shape(text: str) -> str:
    import re
    low = str(text or "").lower()
    for word, name in _SHAPE_WORDS:
        if re.search(rf"\b{word}\b", low):
            return name
    return ""


def geometric_svg(shape: str) -> bytes | None:
    ink, soft, acc = "#1f2937", "#6b7280", "#6366f1"
    head = ('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 400 400" role="img" '
            f'aria-label="{shape}"><rect width="400" height="400" fill="#ffffff"/>'
            f'<g font-family="Helvetica, Arial, sans-serif" font-size="14" fill="{ink}" stroke="{ink}" stroke-width="2.5" '
            'stroke-linejoin="round" stroke-linecap="round">')
    lab = lambda x, y, t, a="middle": f'<text x="{x}" y="{y}" stroke="none" text-anchor="{a}">{t}</text>'
    dim = f'stroke="{soft}" stroke-width="1.5" stroke-dasharray="5 4" fill="none"'
    if shape == "square":
        body = (f'<rect x="100" y="100" width="200" height="200" fill="{acc}" fill-opacity="0.12"/>'
                f'<path d="M100 100 L300 300 M300 100 L100 300" {dim}/>'
                + lab(200, 90, "lato a") + lab(86, 205, "a", "end") + lab(200, 330, "Perimetro = 4a") + lab(200, 352, "Area = a²")
                + lab(200, 190, "d = a√2"))
    elif shape == "rectangle":
        body = (f'<rect x="70" y="120" width="260" height="160" fill="{acc}" fill-opacity="0.12"/>'
                + lab(200, 110, "base b") + lab(56, 205, "h", "end") + lab(200, 315, "Perimetro = 2(b + h)") + lab(200, 337, "Area = b · h"))
    elif shape == "triangle":
        body = (f'<path d="M200 80 L320 300 L80 300 Z" fill="{acc}" fill-opacity="0.12"/>'
                f'<path d="M200 80 L200 300" {dim}/>'
                + lab(200, 322, "base b") + lab(210, 205, "h", "start") + lab(200, 350, "Area = b · h / 2"))
    elif shape == "circle":
        body = (f'<circle cx="200" cy="190" r="110" fill="{acc}" fill-opacity="0.12"/>'
                f'<path d="M200 190 L310 190" {dim}/><circle cx="200" cy="190" r="3" fill="{ink}"/>'
                + lab(255, 182, "r") + lab(200, 330, "Circonferenza = 2πr") + lab(200, 352, "Area = πr²"))
    elif shape == "pyramid":
        body = (f'<path d="M200 70 L320 290 L200 330 L80 290 Z" fill="{acc}" fill-opacity="0.12"/>'
                f'<path d="M200 70 L200 330 M80 290 L320 290" {dim}/>'
                + lab(200, 58, "vertice") + lab(200, 358, "base quadrata, 4 facce triangolari") + lab(206, 200, "h", "start"))
    else:  # cube / box
        w = 1.0 if shape == "cube" else 1.35
        x0, y0, s, dx, dy = 90, 150, 150, 70, -60
        W = s * w
        f = f'M{x0} {y0} h{W} v{s} h{-W} Z'
        top = f'M{x0} {y0} l{dx} {dy} h{W} l{-dx} {-dy} Z'
        side = f'M{x0+W} {y0} l{dx} {dy} v{s} l{-dx} {-dy} Z'
        hidden = f'M{x0} {y0+s} l{dx} {dy} h{W} M{x0+dx} {y0+dy} v{s} M{x0+dx} {y0+s+dy} L{x0+dx} {y0+dy} '
        body = (f'<path d="{f}" fill="{acc}" fill-opacity="0.12"/><path d="{top}" fill="{acc}" fill-opacity="0.22"/>'
                f'<path d="{side}" fill="{acc}" fill-opacity="0.32"/>'
                f'<path d="M{x0+dx} {y0+dy} v{s} M{x0+dx} {y0+s+dy} h{-dx*0} l{-dx} {-dy} M{x0+dx} {y0+s+dy} h{W}" {dim}/>'
                + lab(x0 + W / 2, y0 + s + 24, "spigolo a" if shape == "cube" else "lunghezza l")
                + (lab(200, 345, "8 vertici · 12 spigoli · 6 facce") + lab(200, 367, "Volume = a³ · Superficie = 6a²") if shape == "cube"
                   else lab(200, 345, "8 vertici · 12 spigoli · 6 facce") + lab(200, 367, "Volume = l · w · h")))
    return (head + body + "</g></svg>").encode("utf-8")
