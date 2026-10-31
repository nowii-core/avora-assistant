"""Dataset readers for authorized plain-text and instruction corpora."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterator

TEXT_SUFFIXES = {".txt", ".md", ".jsonl"}
TEXT_FIELDS = ("text", "content", "completion", "output", "body")


def discover_files(path: Path) -> list[Path]:
    path = path.expanduser().resolve()
    if path.is_file():
        return [path] if path.suffix.lower() in TEXT_SUFFIXES else []
    if not path.is_dir():
        return []
    return sorted(
        p for p in path.rglob("*")
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES
        and not any(part.startswith(".") for part in p.relative_to(path).parts)
        and "processed" not in p.parts
    )


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\v\f ]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def _jsonl_to_text(obj: object) -> str | None:
    if not isinstance(obj, dict):
        return None
    for key in TEXT_FIELDS:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_text(value)
    messages = obj.get("messages")
    if isinstance(messages, list):
        parts = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "user")).lower()
            content = message.get("content", message.get("text", ""))
            if isinstance(content, str) and content.strip() and role in {"system", "user", "assistant"}:
                parts.append(f"<|{role}|>\n{normalize_text(content)}")
        return "\n".join(parts) if parts else None
    prompt = obj.get("prompt", obj.get("instruction", obj.get("question")))
    answer = obj.get("completion", obj.get("output", obj.get("answer", obj.get("response"))))
    if isinstance(prompt, str) and isinstance(answer, str) and prompt.strip() and answer.strip():
        return f"<|user|>\n{normalize_text(prompt)}\n<|assistant|>\n{normalize_text(answer)}"
    return None


def iter_documents(path: Path) -> Iterator[tuple[str, str]]:
    """Yield (document_text, source_path) one record at a time."""
    for file_path in discover_files(path):
        try:
            with file_path.open("r", encoding="utf-8", errors="replace") as handle:
                if file_path.suffix.lower() != ".jsonl":
                    text = normalize_text(handle.read())
                    if text:
                        yield text, str(file_path)
                    continue
                for line_no, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = _jsonl_to_text(item)
                    if text and len(text) >= 20:
                        yield text, f"{file_path}:{line_no}"
        except OSError as exc:
            print(f"[avviso] file ignorato {file_path}: {exc}")


def write_combined_text(path: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = chars = 0
    digest = hashlib.sha256()
    with output.open("w", encoding="utf-8") as target:
        for text, source in iter_documents(path):
            target.write(text + "\n\n")
            digest.update(text.encode("utf-8"))
            digest.update(b"\n\n")
            count += 1
            chars += len(text)
    if count == 0:
        output.unlink(missing_ok=True)
        raise SystemExit(f"Nessun testo leggibile in {path}. Aggiungi file .txt, .md o .jsonl.")
    return {"documents": count, "characters": chars, "sha256": digest.hexdigest(), "output": str(output)}
