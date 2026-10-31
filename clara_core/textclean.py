"""Text post-processing for model output: emoji removal, reasoning-tag cleanup and
safe stitching of continued answers.

Everything here is pure and deterministic so it can be unit-tested without Ollama.
"""
from __future__ import annotations

import re

# Pictographic ranges only. Letters, digits, accents, typographic punctuation, the
# command sign and legal marks (c), (R), TM are deliberately left alone.
_EMOJI_CHARS = (
    "\U0001F000-\U0001FAFF"       # emoticons, pictographs, transport, flags, supplemental symbols
    "☀-➿"               # miscellaneous symbols and dingbats
    "⬅-⬇⬛⬜⭐⭕"
    "⌚⌛⏩-⏳⏸-⏺"
    "⤴⤵〰〽㊗㊙"
    "Ⓜ▶◀◻-◾"
)
_EMOJI_ATOM = f"[{_EMOJI_CHARS}]"
_EMOJI_SEQUENCE = re.compile(
    f"{_EMOJI_ATOM}(?:[︎️⃣\U0001F3FB-\U0001F3FF\U000E0020-\U000E007F])*"
    f"(?:‍{_EMOJI_ATOM}[︎️]*)*"
)
_STRAY_MARKS = re.compile("[︎️⃣]")
_THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def contains_emoji(text: str) -> bool:
    return bool(_EMOJI_SEQUENCE.search(text or ""))


def strip_emoji(text: str) -> str:
    """Remove emoji outside fenced code blocks and tidy the whitespace they leave."""
    if not text or not _EMOJI_SEQUENCE.search(text) and not _STRAY_MARKS.search(text):
        return text
    output: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if _FENCE.match(line):
            in_fence = not in_fence
            output.append(line)
            continue
        if in_fence or not (_EMOJI_SEQUENCE.search(line) or _STRAY_MARKS.search(line)):
            output.append(line)
            continue
        cleaned = _EMOJI_SEQUENCE.sub("", line)
        cleaned = _STRAY_MARKS.sub("", cleaned)
        indent = re.match(r"\s*", cleaned).group(0)
        body = cleaned[len(indent):]
        body = re.sub(r"(?<=\S)[ \t]{2,}", " ", body).rstrip()
        body = re.sub(r"[ \t]+(?=[.,;:!?)])", "", body)
        # "- " or "## " followed by nothing once the emoji is gone.
        if re.fullmatch(r"(?:[-*+]|#{1,6}|\d+[.)])", body):
            body = ""
        output.append((indent + body) if body else "")
    return "\n".join(output)


def strip_reasoning(text: str) -> str:
    """Drop <think> blocks that some reasoning models leak into the visible answer."""
    if not text:
        return text
    cleaned = _THINK_BLOCK.sub("", text)
    if "<think>" in cleaned.lower():
        cleaned = re.split(r"<think>", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    return cleaned.replace("</think>", "").strip()


def clean_model_output(text: str) -> str:
    return strip_emoji(strip_reasoning(text or "")).strip()


def inside_code_fence(text: str) -> bool:
    open_fence = False
    for line in text.split("\n"):
        if _FENCE.match(line):
            open_fence = not open_fence
    return open_fence


def trim_to_boundary(text: str) -> str:
    """Cut a possibly half-written trailing token so a continuation can resume cleanly."""
    if not text:
        return text
    if inside_code_fence(text):
        cut = text.rfind("\n")
        return text[: cut + 1] if cut > 0 else text
    if text[-1].isspace() or text[-1] in ".,;:!?)]}\"'`»”":
        return text
    cut = max(text.rfind(" "), text.rfind("\n"), text.rfind("\t"))
    return text[: cut + 1] if cut > 0 else text


def join_continuation(previous: str, continuation: str) -> str:
    """Append a continuation to an answer that stopped at the token limit.

    Removes a re-opened code fence, text the model repeated from the end of the
    previous part, and fixes the spacing at the seam.
    """
    cont = continuation.lstrip("\r")
    if not cont.strip():
        return previous
    if inside_code_fence(previous):
        first, _, rest = cont.lstrip("\n").partition("\n")
        # A fence that carries a language tag re-opens a block that is already open.
        if re.match(r"^\s*```[A-Za-z0-9_+.-]+\s*$", first):
            cont = rest
    window = min(len(previous), len(cont), 400)
    for size in range(window, 9, -1):
        if previous.endswith(cont[:size]):
            cont = cont[size:]
            break
    if not cont.strip():
        return previous
    if previous.endswith(("\n", " ")) or cont.startswith(("\n", " ")):
        return previous + cont
    return previous + (" " if cont[0].isalnum() else "") + cont
