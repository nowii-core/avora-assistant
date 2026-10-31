"""Recognise requests to create an image and turn them into a clean subject.

Kept dependency-free and mirrored by `detectImageRequest` in assets/app.js; the parity
test in tests/test_image_intent.py runs both implementations on the same sentences.
"""
from __future__ import annotations

import re

_NOUNS = (
    r"immagine|immagini|foto|fotografia|fotografie|disegno|disegni|illustrazione|illustrazioni|logo|loghi|marchio|"
    r"poster|locandina|sfondo|sfondi|wallpaper|copertina|ritratto|icona|banner|infografica|schema|schemi|"
    r"diagramma|diagrammi|flowchart|mappa concettuale|grafico matematico|picture|image|illustration|drawing|render|mockup"
)
_VERBS = (
    r"generami|genera|generare|generarmi|generate|generi|creami|crea|creare|crearmi|crei|create|fammi|fai|fare|farmi|"
    r"make|draw|disegnami|disegna|disegnare|disegnarmi|dipingi|dipingimi|realizzami|realizza|realizzare|realizzarmi|"
    r"progettami|progetta|produci|elaborami|elabora"
)
_DRAW_VERBS = r"disegnami|disegna|disegnare|disegnarmi|dipingi|dipingimi|draw"
_DESIRE = r"voglio|vorrei|mi serve|mi servirebbe|mi servono|ho bisogno di|mi occorre|mi occorrono|desidero"
_CORE_NOUNS = r"immagine|foto|fotografia|logo|marchio|illustrazione|poster|locandina|disegno|wallpaper|sfondo|ritratto|icona|banner|copertina"
_NOT_AN_IMAGE_REQUEST = (
    r"\b(?:codice|script|funzione|programma|python|javascript|typescript|html|css|api|classe|libreria|comando|bash|sql|"
    r"react|backend|frontend|algoritmo|pagina web|riga di comando|ridimension\w*|comprim\w*|convert\w*|carica\w*|ottimizz\w*|"
    r"docker|container|dockerfile|come si|come posso|come faccio|tutorial|quale programma|quale app)\b"
)
_QUESTION_START = re.compile(r"^(?:come|perché|perche|spiegami|insegnami|che cosa|cosa significa|quale|quali|dove|quando)\b")


def _norm(text: str) -> str:
    return " ".join(str(text or "").split()).strip().casefold()


def detect_image_request(message: str) -> bool:
    value = _norm(message)
    if not value or len(value) > 12000:
        return False
    if _QUESTION_START.match(value) or re.search(_NOT_AN_IMAGE_REQUEST, value):
        return False
    # "create/make ... <image noun>" with the verb first.
    if re.search(rf"\b(?:{_VERBS})\b[^.?!]{{0,80}}?\b(?:{_NOUNS})\b", value):
        return True
    # Drawing verbs are unambiguous on their own: "disegnami un gatto".
    if re.search(rf"\b(?:{_DRAW_VERBS})\b\s+\S+", value):
        return True
    # "vorrei un logo per ...", "mi serve una foto di ..."
    if re.search(rf"\b(?:{_DESIRE})\b\s+(?:una?|un'|l'|lo|la|delle|dei)?\s*(?:{_CORE_NOUNS})\b", value):
        return True
    # A bare noun phrase such as "foto di un gatto sul divano".
    if len(value) <= 220 and re.match(rf"^(?:{_CORE_NOUNS})\s+(?:di|del|della|dei|delle|con|raffigurante|che raffigura)\b", value):
        return True
    return False


_KIND_PATTERNS = (
    (r"\b(?:foto|fotografia|fotografie|fotorealistic\w+|photo|picture)\b", "fotografia realistica"),
    (r"\b(?:logo|loghi|marchio)\b", "logo professionale"),
    (r"\b(?:icona)\b", "icona"),
    (r"\b(?:disegno|disegni|illustrazione|illustrazioni|dipingi\w*|draw|drawing|illustration)\b", "illustrazione"),
    (r"\b(?:poster|locandina|manifesto|banner)\b", "poster grafico"),
    (r"\b(?:ritratto)\b", "ritratto"),
    (r"\b(?:sfondo|sfondi|wallpaper)\b", "sfondo"),
    (r"\b(?:schema|schemi|diagramma|diagrammi|flowchart|infografica|mappa concettuale|grafico matematico)\b",
     "schema vettoriale con etichette leggibili"),
)


def image_kind(message: str) -> str:
    value = _norm(message)
    for pattern, label in _KIND_PATTERNS:
        if re.search(pattern, value):
            return label
    return "immagine"


def image_composition(message: str) -> str:
    value = _norm(message)
    if re.search(r"verticale|storia instagram|story instagram|formato 9:16|9:16|ritratto verticale", value):
        return "portrait"
    if re.search(r"orizzontale|panoram|16:9|wallpaper desktop|sfondo pc|banner", value):
        return "landscape"
    return "square"


def image_subject(message: str) -> str:
    """Strip politeness, request verbs and the generic noun, leaving what must be drawn."""
    original = " ".join(str(message or "").split()).strip()
    subject = original
    patterns = [
        r"^(?:ciao|ehi|salve)[,!\s]+",
        r"^(?:per favore|per piacere|ti prego|gentilmente)[,\s]*",
        r"^(?:puoi|potresti|riesci a|vorrei che tu|voglio che tu)\s+",
        rf"^(?:{_DESIRE})\s+",
        rf"^(?:mi\s+)?(?:{_VERBS})(?:\s+(?:mi|per favore|per piacere))?\s+",
        r"^(?:(?:un'|l')\s*|(?:una|uno|un|lo|la|dei|delle)\s+)",
        r"^(?:an?|the)\s+(?=(?:image|picture|photo|illustration|drawing|logo)\b)",
        r"^(?:please\s+)?(?:can you\s+)?(?:generate|create|make|draw)\s+(?:me\s+)?",
        rf"^(?:{_NOUNS})\s*",
        r"^(?:of|di)\s+",
        r"^(?:di|del|della|dello|dei|degli|delle|che raffigura|che raffiguri|raffigurante|con)\s+",
    ]
    for _ in range(2):
        for pattern in patterns:
            subject = re.sub(pattern, "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\s*(?:in formato|formato)\s+(?:orizzontale|verticale|quadrato|16:9|9:16)\b", "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\s+(?:per favore|grazie)[.!]*$", "", subject, flags=re.IGNORECASE)
    subject = subject.strip(" ,.:;-")
    return subject or original


def build_image_prompt(message: str) -> tuple[str, str]:
    """Return (display prompt, composition) for a natural-language request."""
    original = " ".join(str(message or "").split()).strip()
    if not original:
        raise ValueError("Scrivi cosa vuoi vedere nell'immagine.")
    prompt = f"Crea un'immagine di alta qualità ({image_kind(original)}): {image_subject(original)}"
    return prompt[:2000], image_composition(original)
