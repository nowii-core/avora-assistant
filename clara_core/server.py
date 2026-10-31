"""Small local HTTP server and JSON API for Avora."""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
import shutil
import base64
import json
import mimetypes
import re
import uuid
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote, quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape as xml_escape

from . import storage
from .runtime import OLLAMA_URL, ClaraRuntime
from .intent_router import build_search_query, classify_intent, intent_instructions, needs_web
from .image_intent import build_image_prompt, detect_image_request as _detect_image_request, image_kind, image_subject
from .svg_art import SvgRejected, build_svg_prompt, detect_geometric_shape, extract_svg, geometric_svg, sanitize_svg
from .textclean import clean_model_output, strip_emoji

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MAX_BODY = 7_500_000
IMAGE_GENERATION_MODEL = "flux"
# Ollama image generation is currently documented for macOS. It keeps prompts and outputs local.
IMAGE_LOCAL_MODEL = os.environ.get("AVORA_IMAGE_MODEL", "x/flux2-klein")
GALLERY_UPLOAD_DIR = ROOT / "data" / "gallery_uploads"
IMAGE_INSTALL_STATE_LOCK = threading.Lock()
IMAGE_INSTALL_STATE = {"active": False, "phase": "idle", "detail": "", "updated_at": None, "error": None}
IMAGE_PROVIDER_CONFIG = ROOT / "data" / "image_provider.json"
IMAGE_PROVIDER_CONSENT_CONFIG = ROOT / "data" / "image_provider_consent.json"
IMAGE_OUTPUT_DIR = ROOT / "data" / "generated_images"
_IMAGE_GENERATION_LOCK = threading.Lock()
MAX_GENERATED_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_MIMES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
RUNTIME = ClaraRuntime()
_PROGRESS_LOCK = threading.Lock()
_PROGRESS_STATE = {
    "active": False, "phase": "idle", "detail": "In attesa di una richiesta.",
    "started_at": None, "updated_at": None, "generated_tokens": 0,
    "partial_text": "", "sources_count": 0, "images_count": 0,
}


def update_progress(phase: str, detail: str, **extra) -> None:
    with _PROGRESS_LOCK:
        _PROGRESS_STATE.update({"active": True, "phase": phase, "detail": detail,
                                "updated_at": time.time(), **extra})


def begin_progress(images_count: int = 0, deep_research: bool = False) -> None:
    now = time.time()
    with _PROGRESS_LOCK:
        _PROGRESS_STATE.update({
            "active": True, "phase": "validating", "detail": "Verifica della richiesta e del budget token.",
            "started_at": now, "updated_at": now, "generated_tokens": 0,
            "partial_text": "", "sources_count": 0, "images_count": images_count,
            "deep_research": deep_research,
        })


def finish_progress(phase: str = "done", detail: str = "Richiesta completata.", **extra) -> None:
    with _PROGRESS_LOCK:
        _PROGRESS_STATE.update({"active": False, "phase": phase, "detail": detail,
                                "updated_at": time.time(), **extra})


def progress_snapshot() -> dict:
    with _PROGRESS_LOCK:
        return dict(_PROGRESS_STATE)


def load_image_provider_key() -> str:
    """Load a local-only Pollinations secret without ever returning it to the browser."""
    try:
        data = json.loads(IMAGE_PROVIDER_CONFIG.read_text(encoding="utf-8"))
        key = str(data.get("api_key", "")).strip()
        return key if key.startswith("sk_") and len(key) >= 12 else ""
    except (OSError, ValueError, AttributeError, TypeError):
        return ""


def save_image_provider_key(value: object) -> bool:
    key = str(value or "").strip()
    IMAGE_PROVIDER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not key:
        try:
            IMAGE_PROVIDER_CONFIG.unlink()
        except FileNotFoundError:
            pass
        return False
    if not key.startswith("sk_") or len(key) < 12 or len(key) > 512 or any(ch.isspace() for ch in key):
        raise ValueError("La chiave deve essere una chiave privata Pollinations valida (prefisso sk_).")
    temp_path = IMAGE_PROVIDER_CONFIG.with_suffix(".tmp")
    temp_path.write_text(json.dumps({"api_key": key}, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(temp_path, 0o600)
    except OSError:
        pass
    temp_path.replace(IMAGE_PROVIDER_CONFIG)
    try:
        os.chmod(IMAGE_PROVIDER_CONFIG, 0o600)
    except OSError:
        pass
    return True


def load_image_provider_consent() -> bool:
    """Whether the user explicitly agreed to send image prompts to the free AI Horde."""
    try:
        value = json.loads(IMAGE_PROVIDER_CONSENT_CONFIG.read_text(encoding="utf-8"))
        return bool(isinstance(value, dict) and value.get("provider") == "aihorde" and value.get("consent") is True)
    except (OSError, ValueError, TypeError):
        return False


def save_image_provider_consent(consent: object) -> bool:
    """Store one-time consent locally; anonymous AI Horde prompts leave this Mac."""
    if consent is not True:
        try:
            IMAGE_PROVIDER_CONSENT_CONFIG.unlink()
        except FileNotFoundError:
            pass
        return False
    IMAGE_PROVIDER_CONSENT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temp_path = IMAGE_PROVIDER_CONSENT_CONFIG.with_suffix(".tmp")
    temp_path.write_text(json.dumps({"provider": "aihorde", "consent": True}, indent=2), encoding="utf-8")
    try:
        os.chmod(temp_path, 0o600)
    except OSError:
        pass
    temp_path.replace(IMAGE_PROVIDER_CONSENT_CONFIG)
    try:
        os.chmod(IMAGE_PROVIDER_CONSENT_CONFIG, 0o600)
    except OSError:
        pass
    return True


def _ollama_binary() -> str | None:
    """Find the Ollama CLI on common macOS/Homebrew paths as well as PATH."""
    found = shutil.which("ollama")
    if found:
        return found
    for candidate in ("/opt/homebrew/bin/ollama", "/usr/local/bin/ollama", "/usr/bin/ollama"):
        if Path(candidate).is_file():
            return candidate
    return None


def ollama_image_model_installed() -> bool:
    """Return True only when the configured image model is already installed."""
    binary = _ollama_binary()
    if not binary:
        return False
    try:
        result = subprocess.run([binary, "list"], capture_output=True, text=True, timeout=12, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines()[1:]:
        name = line.split()[0] if line.split() else ""
        if name == IMAGE_LOCAL_MODEL or name.startswith(IMAGE_LOCAL_MODEL + ":"):
            return True
    return False


def image_install_snapshot() -> dict:
    installed = ollama_image_model_installed()
    with IMAGE_INSTALL_STATE_LOCK:
        return {**IMAGE_INSTALL_STATE, "model": IMAGE_LOCAL_MODEL, "installed": installed}


def _image_install_worker() -> None:
    binary = _ollama_binary()
    if not binary:
        with IMAGE_INSTALL_STATE_LOCK:
            IMAGE_INSTALL_STATE.update(active=False, phase="error", detail="Ollama non è installato o non è stato trovato.", error="ollama_missing", updated_at=time.time())
        return
    try:
        with IMAGE_INSTALL_STATE_LOCK:
            IMAGE_INSTALL_STATE.update(active=True, phase="downloading", detail=f"Scarico {IMAGE_LOCAL_MODEL}. Servono diversi GB e può volerci del tempo.", error=None, updated_at=time.time())
        process = subprocess.Popen([binary, "pull", IMAGE_LOCAL_MODEL], cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert process.stdout is not None
        for line in process.stdout:
            clean = " ".join(line.split())
            if clean:
                # Limit terminal-provided text and keep state safe to display as text.
                with IMAGE_INSTALL_STATE_LOCK:
                    IMAGE_INSTALL_STATE.update(active=True, phase="downloading", detail=clean[:240], updated_at=time.time())
        code = process.wait(timeout=1800)
        if code != 0:
            raise RuntimeError(f"ollama pull è terminato con codice {code}. Aggiorna Ollama e riprova.")
        if not ollama_image_model_installed():
            raise RuntimeError("Il download è terminato ma il modello immagini non appare in 'ollama list'. Aggiorna Ollama e verifica il modello.")
        with IMAGE_INSTALL_STATE_LOCK:
            IMAGE_INSTALL_STATE.update(active=False, phase="done", detail=f"{IMAGE_LOCAL_MODEL} è installato. Puoi generare immagini localmente.", error=None, updated_at=time.time())
    except Exception as exc:
        with IMAGE_INSTALL_STATE_LOCK:
            IMAGE_INSTALL_STATE.update(active=False, phase="error", detail=str(exc)[:400], error=type(exc).__name__, updated_at=time.time())


def start_image_model_install() -> dict:
    installed = ollama_image_model_installed()
    with IMAGE_INSTALL_STATE_LOCK:
        if IMAGE_INSTALL_STATE.get("active"):
            return {**IMAGE_INSTALL_STATE, "model": IMAGE_LOCAL_MODEL, "installed": installed}
        if installed:
            IMAGE_INSTALL_STATE.update(active=False, phase="done", detail=f"{IMAGE_LOCAL_MODEL} è già installato.", error=None, updated_at=time.time())
            return {**IMAGE_INSTALL_STATE, "model": IMAGE_LOCAL_MODEL, "installed": True}
        binary = _ollama_binary()
        if not binary:
            IMAGE_INSTALL_STATE.update(active=False, phase="error", detail="Ollama non è installato o non è stato trovato.", error="ollama_missing", updated_at=time.time())
            return {**IMAGE_INSTALL_STATE, "model": IMAGE_LOCAL_MODEL, "installed": False}
        IMAGE_INSTALL_STATE.update(active=True, phase="starting", detail=f"Avvio il download di {IMAGE_LOCAL_MODEL}. Il modello occupa diversi GB.", error=None, updated_at=time.time())
    threading.Thread(target=_image_install_worker, name="avora-image-model-install", daemon=True).start()
    return image_install_snapshot()


def image_generation_status() -> dict:
    """Describe image backends without exposing API keys or implying that a backend is ready."""
    key_configured = bool(load_image_provider_key())
    local_installed = ollama_image_model_installed()
    horde = load_image_provider_consent()
    install = image_install_snapshot()
    try:
        diagram_available = bool(RUNTIME.status().get("model_loaded"))
    except Exception:
        diagram_available = False
    if local_installed:
        provider, quality = "Ollama locale", "photo"
        reason = f"Generatore fotografico locale pronto ({IMAGE_LOCAL_MODEL}). Prompt e immagini restano su questo computer."
    elif key_configured:
        provider, quality = "Pollinations API", "photo"
        reason = "Generatore online configurato: il prompt viene inviato a Pollinations e l'uso può consumare crediti."
    elif horde:
        provider, quality = "AI Horde", "photo"
        reason = "Rete gratuita AI Horde attiva: il prompt viene inviato in forma anonima a worker volontari. Possibili attese in coda."
    else:
        provider, quality = "Illustrazioni locali", "vector"
        reason = ("Le immagini vengono disegnate in locale come illustrazioni vettoriali e schemi, senza download. "
                  "Per immagini fotorealistiche installa il generatore locale o attiva la rete gratuita online." if diagram_available else
                  "Per creare immagini serve il modello testuale locale funzionante (Ollama).")
    return {
        "supported": True,
        "available": bool(diagram_available or local_installed or key_configured or horde),
        "configured": key_configured,
        "consent": horde,
        "needs_consent": False,
        "horde_enabled": horde,
        "quality": quality,
        "provider": provider,
        "model": IMAGE_LOCAL_MODEL if local_installed else (IMAGE_GENERATION_MODEL if key_configured else "illustrazione"),
        "local_model": IMAGE_LOCAL_MODEL,
        "local_model_installed": local_installed,
        "diagram_available": diagram_available,
        "install": install,
        "setup_url": "https://ollama.com/blog/image-generation",
        "reason": reason,
    }


def _generated_path(image_id: str) -> Path | None:
    if not re.fullmatch(r"[a-f0-9]{32}", image_id):
        return None
    for suffix in (".png", ".webp", ".jpg", ".jpeg", ".svg"):
        candidate = IMAGE_OUTPUT_DIR / f"{image_id}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def list_generated_images() -> list[dict]:
    IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = []
    for meta_path in sorted(IMAGE_OUTPUT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            item = json.loads(meta_path.read_text(encoding="utf-8"))
            image_id = str(item.get("id", meta_path.stem))
            image_path = _generated_path(image_id)
            if not image_path:
                continue
            item["url"] = f"/api/generated/{image_id}"
            item["filename"] = f"avora-{image_id}{image_path.suffix}"
            output.append(item)
        except (OSError, ValueError, AttributeError):
            continue
    return output[:60]


def _gallery_upload_path(image_id: str) -> Path | None:
    if not re.fullmatch(r"[a-f0-9]{32}", image_id):
        return None
    for suffix in (".png", ".jpg", ".webp"):
        candidate = GALLERY_UPLOAD_DIR / f"{image_id}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def list_gallery_uploads() -> list[dict]:
    GALLERY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output = []
    for meta_path in sorted(GALLERY_UPLOAD_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            item = json.loads(meta_path.read_text(encoding="utf-8"))
            image_id = str(item.get("id", meta_path.stem))
            image_path = _gallery_upload_path(image_id)
            if not image_path:
                continue
            item.update({"id": image_id, "url": f"/api/gallery/uploads/{image_id}",
                         "filename": item.get("filename") or image_path.name, "kind": "uploaded", "origin": "Caricata nella galleria"})
            output.append(item)
        except (OSError, ValueError, TypeError):
            continue
    return output[:80]


def list_chat_uploaded_images() -> list[dict]:
    """Find all user-attached images in saved chats, newest first."""
    output = []
    for item in storage.list_image_attachments(limit=1500):
        output.append({
            "id": item["id"], "url": item["url"], "filename": item["name"],
            "prompt": item["content"][:500] or "Immagine caricata in chat",
            "created_at": item["created_at"], "kind": "uploaded",
            "origin": "Allegata in chat", "mime": item["mime"],
            "conversation_id": item["conversation_id"],
        })
    return output[:120]


def list_image_gallery() -> dict:
    generated = [{**item, "kind": "generated", "origin": "Creata da Avora"} for item in list_generated_images()]
    uploads = list_gallery_uploads() + list_chat_uploaded_images()
    unique_uploads = []
    seen: set[str] = set()
    for item in uploads:
        key = str(item.get("id", ""))
        if key and key not in seen:
            seen.add(key)
            unique_uploads.append(item)
    gallery = sorted(generated + unique_uploads, key=lambda item: str(item.get("created_at", "")), reverse=True)[:180]
    return {"images": generated, "uploads": unique_uploads[:120], "gallery": gallery}


def save_gallery_upload(filename: object, mime: object, data: object) -> dict:
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", str(filename or "immagine"))[:100].strip() or "immagine"
    content_type = str(mime or "").lower().strip()
    if content_type not in IMAGE_MIMES:
        raise ValueError("Formato non supportato: usa PNG, JPEG o WebP.")
    expected_suffix = IMAGE_MIMES[content_type]
    if not name.lower().endswith(expected_suffix):
        stem = Path(name).stem[:90].strip() or "immagine"
        name = stem + expected_suffix
    if not isinstance(data, str) or not data:
        raise ValueError("Il file immagine è vuoto.")
    try:
        binary = base64.b64decode(data, validate=True)
    except Exception as exc:
        raise ValueError("Il file immagine non è valido.") from exc
    if not binary or len(binary) > MAX_IMAGE_BYTES:
        raise ValueError("Ogni immagine deve essere inferiore a 5 MB.")
    expected_signatures = {
        "image/png": lambda value: value.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/jpeg": lambda value: value.startswith(b"\xff\xd8\xff"),
        "image/webp": lambda value: value.startswith(b"RIFF") and value[8:12] == b"WEBP",
    }
    if not expected_signatures[content_type](binary):
        raise ValueError("Il contenuto del file non corrisponde al formato immagine dichiarato.")
    GALLERY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_id = uuid.uuid4().hex
    suffix = IMAGE_MIMES[content_type]
    target = GALLERY_UPLOAD_DIR / f"{image_id}{suffix}"
    target.write_bytes(binary)
    metadata = {"id": image_id, "filename": name, "mime": content_type,
                "prompt": "Immagine caricata dall'utente", "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "kind": "uploaded", "origin": "Caricata nella galleria", "url": f"/api/gallery/uploads/{image_id}"}
    (GALLERY_UPLOAD_DIR / f"{image_id}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(target, 0o600)
        os.chmod(GALLERY_UPLOAD_DIR / f"{image_id}.json", 0o600)
    except OSError:
        pass
    return metadata


def normalize_image_prompt(message: str) -> tuple[str, str]:
    """Turn natural chat requests into an image prompt and aspect ratio."""
    return build_image_prompt(message)


class ImageProviderNotConfigured(RuntimeError):
    pass


def generate_image_chat_turn(message: str, prompt: str, composition: str = "square",
                             conversation_id: str | None = None) -> dict:
    """Generate an image directly from a chat request and persist it in chat history."""
    original = " ".join(str(message or "").split()).strip()
    clean_prompt, inferred_composition = normalize_image_prompt(original)
    if isinstance(prompt, str) and prompt.strip():
        # Frontend may provide an explicit cleaned prompt; keep server-side normalization as fallback.
        clean_prompt = " ".join(prompt.split())[:2000]
    if composition not in {"square", "portrait", "landscape"}:
        composition = inferred_composition
    generated = generate_image_local(clean_prompt, composition, original_request=original)

    existing = storage.get_conversation(conversation_id) if isinstance(conversation_id, str) and re.fullmatch(r"[a-f0-9]{32}", conversation_id) else None
    conversation = existing or storage.create_conversation((original[:53] + ("…" if len(original) > 53 else "")) or "Immagine")
    conversation_id = conversation["id"]
    extension = Path(generated["filename"]).suffix.lower()
    image_attachment = {
        "generated": True,
        "generated_image_id": generated["id"],
        "url": generated["url"],
        "name": generated["filename"],
        "mime": {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}.get(extension, "image/jpeg"),
        "prompt": clean_prompt,
    }
    user_message = storage.add_message(conversation_id, "user", original)
    assistant_message = storage.add_message(conversation_id, "assistant", _image_reply_text(generated), [image_attachment])
    return {
        "conversation_id": conversation_id,
        "conversation": storage.get_conversation(conversation_id),
        "user_message": user_message,
        "assistant_message": assistant_message,
        "image": generated,
        "mode": "image-generation",
    }


def compact_conversation(conversation_id: str) -> dict:
    """Summarise a long chat into a new one that keeps the essential context."""
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise KeyError("Conversazione non trovata")
    messages = [m for m in storage.get_messages(conversation_id) if m.get("role") in {"user", "assistant"}]
    if len(messages) < 2:
        raise ValueError("La conversazione è troppo breve per essere riassunta.")
    lines: list[str] = []
    total = 0
    for item in reversed(messages):
        who = "Utente" if item["role"] == "user" else "Assistente"
        text = " ".join(str(item.get("content", "")).split())[:1500]
        total += len(text)
        if total > 12000:
            break
        lines.append(f"{who}: {text}")
    transcript = "\n".join(reversed(lines))
    summary = _ollama_text(
        "Riassumi la conversazione seguente in italiano per permettere di proseguirla senza rileggerla. "
        "Includi: obiettivo dell'utente, decisioni prese, fatti e numeri importanti, codice o nomi di file citati, punti ancora aperti. "
        "Usa un elenco puntato, massimo 250 parole, senza inventare nulla.\n\n" + transcript,
        num_predict=700, temperature=0.2, timeout=240,
        system="Sei un assistente che scrive riassunti fedeli e compatti.")
    from .textclean import clean_model_output
    summary = clean_model_output(summary).strip()
    if not summary:
        raise RuntimeError("Il modello non ha prodotto un riassunto. Riprova.")
    title = "Continua: " + str(conversation.get("title", "chat"))[:60]
    new_conversation = storage.create_conversation(title)
    storage.add_message(new_conversation["id"], "user", "Riassunto del contesto della chat precedente, da usare come memoria:\n\n" + summary)
    storage.add_message(new_conversation["id"], "assistant", "Ho il contesto della chat precedente. Come vuoi proseguire?")
    return storage.get_conversation(new_conversation["id"]) or new_conversation


def _tool_attachments(metrics: dict) -> list[dict]:
    """Charts/files produced by the agent become stored images; the tool trace is kept for display."""
    items: list[dict] = []
    for tool in metrics.get("tools", []) or []:
        items.append({"tool": True, "name": str(tool.get("name", ""))[:40], "ok": bool(tool.get("ok", True)),
                      "input": str(tool.get("input", ""))[:4000], "output": str(tool.get("output", ""))[:1500]})
    for image in metrics.get("tool_images", []) or []:
        try:
            raw = base64.b64decode(image.get("data", ""), validate=True)
            record = _persist_generated_image(f"Grafico: {image.get('name', 'risultato')}", "square", raw, str(image.get("mime", "")), "Sandbox Python", "python")
        except Exception:
            continue
        items.append({"generated": True, "generated_image_id": record["id"], "url": record["url"], "name": record["filename"],
                      "mime": str(image.get("mime", "image/png")), "prompt": record["prompt"]})
    return items


def _image_reply_text(generated: dict) -> str:
    provider = str(generated.get("provider", ""))
    if generated.get("filename", "").endswith(".svg"):
        if "Schema" in provider:
            return "Ecco lo schema richiesto. Controlla etichette e contenuti prima di riutilizzarlo."
        return ("Ho creato un'illustrazione vettoriale con il modello locale. Per immagini fotorealistiche attiva un generatore "
                "dal pannello Immagini (modello locale oppure rete gratuita online).")
    return "Ecco l'immagine richiesta."


def _persist_generated_image(prompt: str, composition: str, image_bytes: bytes, content_type: str,
                             provider: str, model: str) -> dict:
    if len(image_bytes) > MAX_GENERATED_IMAGE_BYTES:
        raise RuntimeError("L'immagine restituita supera il limite locale di 20 MB.")
    suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/svg+xml": ".svg"}.get(content_type)
    if not suffix or not image_bytes:
        raise RuntimeError("Il servizio non ha restituito un file immagine valido.")
    valid_signature = (
        (content_type == "image/png" and image_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        or (content_type == "image/jpeg" and image_bytes.startswith(b"\xff\xd8\xff"))
        or (content_type == "image/webp" and image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP")
        or (content_type == "image/svg+xml" and image_bytes.lstrip().startswith((b"<svg", b"<?xml")) and b"<script" not in image_bytes.lower())
    )
    if not valid_signature:
        raise RuntimeError("Il provider non ha restituito un contenuto coerente con il tipo immagine dichiarato.")
    IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image_id = uuid.uuid4().hex
    target = IMAGE_OUTPUT_DIR / f"{image_id}{suffix}"
    target.write_bytes(image_bytes)
    record = {
        "id": image_id, "prompt": prompt, "composition": composition,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "provider": provider, "model": model, "kind": "generated", "origin": "Creata da Avora",
        "url": f"/api/generated/{image_id}", "filename": target.name,
    }
    meta_path = IMAGE_OUTPUT_DIR / f"{image_id}.json"
    meta_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(meta_path, 0o600)
    except OSError:
        pass
    return record


def _horde_json(url: str, payload: dict | None = None, timeout: int = 10) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=body, headers={
        "apikey": "0000000000",
        "Client-Agent": "AvoraLocal:1.4.0:local-assistant",
        "Accept": "application/json",
        **({"Content-Type": "application/json"} if body is not None else {}),
    })
    with urlopen(request, timeout=timeout) as response:
        data = response.read(1_000_000).decode("utf-8", errors="replace")
    try:
        result = json.loads(data)
    except ValueError as exc:
        raise RuntimeError("AI Horde ha restituito una risposta inattesa.") from exc
    if not isinstance(result, dict):
        raise RuntimeError("AI Horde ha restituito dati non validi.")
    return result


def _generate_image_ai_horde(prompt: str, composition: str) -> dict:
    """Free community-hosted generation. Anonymous jobs can wait in a shared queue."""
    dimensions = {"square": (512, 512), "portrait": (384, 640), "landscape": (640, 384)}
    width, height = dimensions.get(composition, dimensions["square"])
    base = "https://aihorde.net/api/v2"
    payload = {
        "prompt": prompt,
        "params": {"width": width, "height": height, "steps": 20, "n": 1,
                     "cfg_scale": 7.0, "sampler_name": "k_euler_a", "karras": True},
        "nsfw": False, "censor_nsfw": True, "r2": True, "shared": True,
    }
    update_progress("generating", "Invio il prompt alla rete gratuita di immagini…")
    try:
        submitted = _horde_json(f"{base}/generate/async", payload, timeout=15)
    except HTTPError as exc:
        if exc.code == 429:
            raise RuntimeError("AI Horde sta ricevendo troppe richieste anonime. Attendi e riprova.") from exc
        raise RuntimeError(f"La rete gratuita di immagini ha risposto con HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Non riesco a raggiungere AI Horde. Controlla la connessione Internet.") from exc
    request_id = str(submitted.get("id", ""))
    if not re.fullmatch(r"[a-f0-9-]{16,64}", request_id, re.I):
        message = str(submitted.get("message", ""))
        raise RuntimeError(message or "AI Horde non ha accettato la richiesta. Riprova tra poco.")
    deadline = time.monotonic() + 240
    last_status = {}
    while time.monotonic() < deadline:
        try:
            check = _horde_json(f"{base}/generate/check/{request_id}", timeout=12)
        except (HTTPError, URLError, TimeoutError, RuntimeError):
            time.sleep(2)
            continue
        last_status = check
        if check.get("faulted"):
            raise RuntimeError("La rete di generazione non ha potuto completare l'immagine. Prova un prompt diverso.")
        if check.get("done"):
            break
        queue_position = check.get("queue_position")
        wait_time = check.get("wait_time")
        if isinstance(queue_position, int):
            detail = f"Immagine in coda gratuita: posizione {queue_position}. I tempi dipendono dai worker volontari."
        elif isinstance(wait_time, (int, float)) and wait_time > 0:
            detail = f"Immagine in elaborazione nella rete gratuita: attesa stimata {int(wait_time)} secondi."
        else:
            detail = "Immagine in attesa di un worker volontario."
        update_progress("generating", detail)
        time.sleep(2)
    else:
        try:
            request = Request(f"{base}/generate/status/{request_id}", method="DELETE", headers={"apikey": "0000000000", "Client-Agent": "AvoraLocal:1.4.0:local-assistant"})
            with urlopen(request, timeout=8):
                pass
        except Exception:
            pass
        raise RuntimeError("La coda gratuita non ha completato l'immagine entro 4 minuti. Puoi riprovare; non è stato effettuato alcun acquisto.")
    try:
        status = _horde_json(f"{base}/generate/status/{request_id}", timeout=15)
    except Exception as exc:
        raise RuntimeError("La generazione risulta completata ma non riesco a recuperare l'immagine. Riprova.") from exc
    generations = status.get("generations") or []
    image_url = str(generations[0].get("img", "")) if generations and isinstance(generations[0], dict) else ""
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("AI Horde non ha fornito un link immagine valido.")
    try:
        request = Request(image_url, headers={"User-Agent": "AvoraLocal/1.4.0", "Accept": "image/png,image/jpeg,image/webp"})
        with urlopen(request, timeout=30) as response:
            content_type = (response.headers.get("Content-Type") or "image/webp").split(";", 1)[0].strip().lower()
            image_bytes = response.read(MAX_GENERATED_IMAGE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("L'immagine è stata creata ma non è stato possibile scaricarla.") from exc
    if content_type not in IMAGE_MIMES:
        # Some R2 links omit a useful MIME type; signatures allow a safe fallback.
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            content_type = "image/png"
        elif image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
            content_type = "image/webp"
        elif image_bytes.startswith(b"\xff\xd8\xff"):
            content_type = "image/jpeg"
        else:
            raise RuntimeError("AI Horde non ha restituito un file immagine riconoscibile.")
    record = _persist_generated_image(prompt, composition, image_bytes, content_type, "AI Horde (worker volontari)", str(generations[0].get("model", "modello comunitario")))
    return record


def is_diagram_prompt(prompt: str) -> bool:
    value = str(prompt or "").casefold()
    return bool(re.search(r"\b(?:schema|schemi|diagramma|diagrammi|mappa concettuale|flowchart|infografica|grafico matematico|diagramma di flusso|schema matematico|schema logico)\b", value))


def _diagram_model_json(prompt: str) -> dict:
    """Ask the configured local text model for a small, structured diagram specification."""
    model = getattr(RUNTIME, "model_name", "qwen3:1.7b")
    instruction = (
        "Crea uno schema didattico in italiano a partire dalla richiesta. Restituisci SOLO JSON valido con "
        'questo schema: {"title":"titolo breve","subtitle":"sottotitolo breve","nodes":[{"id":"a","label":"etichetta breve"}],'
        '"edges":[{"from":"a","to":"b","label":""}]}. '
        "Da 3 a 8 nodi, massimo 55 caratteri per etichetta, 1-10 collegamenti. Ordina i nodi in modo leggibile; preferisci un percorso verticale dall'alto in basso. "
        "Non inserire Markdown, HTML, SVG, codice, istruzioni o testo fuori dal JSON. Usa solo fatti didattici di base; se la richiesta è matematica, conserva esattamente formule e simboli nel testo dei nodi. "
        f"Richiesta utente: {prompt[:1400]}"
    )
    raw = _ollama_text(instruction, num_predict=1400, temperature=0.15, timeout=180, json_mode=True)
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("Il modello locale non ha restituito dati validi per lo schema.")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError:
        first, last = raw.find("{"), raw.rfind("}")
        if first < 0 or last <= first:
            raise RuntimeError("Il modello non ha prodotto uno schema leggibile. Riprova con una richiesta più breve.")
        try:
            spec = json.loads(raw[first:last + 1])
        except json.JSONDecodeError as exc:
            raise RuntimeError("Il modello ha restituito uno schema non valido. Riprova con una richiesta più breve.") from exc
    if not isinstance(spec, dict) or not isinstance(spec.get("nodes"), list):
        raise RuntimeError("Lo schema restituito non ha una struttura valida.")
    nodes = []
    seen = set()
    for index, item in enumerate(spec["nodes"][:8]):
        if not isinstance(item, dict):
            continue
        label = " ".join(str(item.get("label", "")).split())[:55]
        node_id = re.sub(r"[^a-zA-Z0-9_-]", "", str(item.get("id", f"n{index}")))[:24] or f"n{index}"
        if not label or node_id in seen:
            continue
        seen.add(node_id)
        nodes.append({"id": node_id, "label": label})
    if len(nodes) < 3:
        raise RuntimeError("Il modello ha restituito meno di tre passaggi; rendi la richiesta più specifica e riprova.")
    valid_ids = {node["id"] for node in nodes}
    edges = []
    for item in spec.get("edges", [])[:12] if isinstance(spec.get("edges", []), list) else []:
        if not isinstance(item, dict):
            continue
        source, target = str(item.get("from", "")), str(item.get("to", ""))
        if source in valid_ids and target in valid_ids and source != target:
            edges.append({"from": source, "to": target, "label": " ".join(str(item.get("label", "")).split())[:35]})
    if not edges:
        edges = [{"from": nodes[i]["id"], "to": nodes[i + 1]["id"], "label": ""} for i in range(len(nodes) - 1)]
    return {
        "title": " ".join(str(spec.get("title", "Schema" )).split())[:100] or "Schema",
        "subtitle": " ".join(str(spec.get("subtitle", "Schema generato localmente")).split())[:150],
        "nodes": nodes,
        "edges": edges,
    }


def _wrap_diagram_label(value: str, width: int = 36, max_lines: int = 3) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max(1, width - 1)].rstrip() + "…"
    return lines or [""]


def _escape_xml_attr(value: object) -> str:
    """Escape XML attribute values as well as element text."""
    return xml_escape(str(value), {'"': "&quot;", "'": "&apos;"})


def render_diagram_svg(spec: dict) -> bytes:
    """Render diagram JSON as a safe, crisp local SVG. No model-produced markup is inserted."""
    nodes = spec["nodes"][:8]
    width = 920
    card_width = 730
    card_x = (width - card_width) // 2
    top = 150
    row_gap = 145
    card_height = 86
    height = top + max(1, len(nodes)) * row_gap + 85
    positions: dict[str, tuple[int, int]] = {}
    fragments = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_escape_xml_attr(spec["title"])}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<path d="M0 0H920V9H0Z" fill="#1f2937"/>',
        f'<text x="{width/2}" y="59" text-anchor="middle" fill="#111827" font-family="-apple-system,BlinkMacSystemFont,Arial,sans-serif" font-size="27" font-weight="700">{xml_escape(spec["title"])}</text>',
        f'<text x="{width/2}" y="88" text-anchor="middle" fill="#6b7280" font-family="-apple-system,BlinkMacSystemFont,Arial,sans-serif" font-size="13">{xml_escape(spec["subtitle"])}</text>',
    ]
    node_by_id = {node["id"]: node for node in nodes}
    edges = spec.get("edges", [])
    for i, node in enumerate(nodes):
        y = top + i * row_gap
        positions[node["id"]] = (card_x + card_width // 2, y + card_height // 2)
    edge_pairs = set()
    for edge in edges:
        source, target = edge["from"], edge["to"]
        if source not in positions or target not in positions or (source, target) in edge_pairs:
            continue
        edge_pairs.add((source, target))
        sx, sy = positions[source]
        tx, ty = positions[target]
        mid_y = (sy + ty) / 2
        fragments.append(f'<path d="M {sx} {sy+card_height/2-1} V {mid_y} H {tx} V {ty-card_height/2+1}" fill="none" stroke="#9ca3af" stroke-width="2"/>')
        fragments.append(f'<path d="M {tx-5} {ty-card_height/2+7} L {tx} {ty-card_height/2+1} L {tx+5} {ty-card_height/2+7}" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
        edge_label = str(edge.get("label", ""))[:35]
        if edge_label:
            fragments.append(f'<text x="{sx+10}" y="{mid_y-4}" fill="#6b7280" font-family="-apple-system,BlinkMacSystemFont,Arial,sans-serif" font-size="11">{xml_escape(edge_label)}</text>')
    for index, node in enumerate(nodes):
        x, ycenter = positions[node["id"]]
        y = ycenter - card_height // 2
        fragments.append(f'<rect x="{card_x}" y="{y}" width="{card_width}" height="{card_height}" rx="13" fill="#fafafa" stroke="#d1d5db" stroke-width="1.4"/>')
        fragments.append(f'<circle cx="{card_x+34}" cy="{ycenter}" r="15" fill="#111827"/>')
        fragments.append(f'<text x="{card_x+34}" y="{ycenter+4}" text-anchor="middle" fill="#ffffff" font-family="-apple-system,BlinkMacSystemFont,Arial,sans-serif" font-size="12" font-weight="650">{index+1}</text>')
        lines = _wrap_diagram_label(node["label"], 66, 3)
        start_y = ycenter - ((len(lines)-1) * 8)
        for line_index, line in enumerate(lines):
            fragments.append(f'<text x="{card_x+65}" y="{start_y+line_index*18+5}" fill="#1f2937" font-family="-apple-system,BlinkMacSystemFont,Arial,sans-serif" font-size="15" font-weight="550">{xml_escape(line)}</text>')
    fragments.append(f'<text x="{width/2}" y="{height-25}" text-anchor="middle" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Arial,sans-serif" font-size="10">Schema locale · verifica i dati importanti</text>')
    fragments.append('</svg>')
    return "".join(fragments).encode("utf-8")


def generate_diagram_local(prompt: str, composition: str = "portrait") -> dict:
    update_progress("generating", "Preparo uno schema vettoriale con etichette leggibili usando il modello locale…")
    spec = _diagram_model_json(prompt)
    svg = render_diagram_svg(spec)
    return _persist_generated_image(prompt, composition, svg, "image/svg+xml", "Schema vettoriale locale", getattr(RUNTIME, "model_name", "modello Ollama"))


def _generate_image_ollama(prompt: str, composition: str) -> dict:
    """Generate an image using Ollama's macOS image-generation CLI in an isolated temp folder."""
    binary = _ollama_binary()
    if not binary:
        raise ImageProviderNotConfigured("Ollama non è stato trovato. Aprilo da Applicazioni e riavvia Avora.")
    if not ollama_image_model_installed():
        raise ImageProviderNotConfigured(f"Il modello immagini {IMAGE_LOCAL_MODEL} non è installato. Apri Immagini e premi Installazione modello locale.")
    update_progress("generating", f"Generazione locale con {IMAGE_LOCAL_MODEL}. Il prompt e il risultato restano su questo Mac…")
    with tempfile.TemporaryDirectory(prefix="avora-image-output-") as temp_dir:
        try:
            result = subprocess.run(
                [binary, "run", IMAGE_LOCAL_MODEL, prompt], cwd=temp_dir,
                capture_output=True, text=True, timeout=900, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("La generazione locale ha superato 15 minuti. Prova un'immagine più semplice o verifica la memoria disponibile.") from exc
        except OSError as exc:
            raise RuntimeError("Non riesco ad avviare Ollama per generare l'immagine.") from exc
        image_candidates = []
        for item in Path(temp_dir).rglob("*"):
            if item.is_file() and item.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                try:
                    if item.stat().st_size > 0:
                        image_candidates.append(item)
                except OSError:
                    pass
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip().splitlines()
            safe_detail = " ".join(detail[-3:])[:280]
            raise RuntimeError(f"Ollama non ha generato l'immagine. Verifica che la tua versione supporti la generazione immagini e sia aggiornata. {safe_detail}".strip())
        if not image_candidates:
            output = (result.stdout or "").strip().splitlines()
            safe_output = " ".join(output[-3:])[:240]
            raise RuntimeError("Ollama ha terminato senza salvare un file immagine nel percorso temporaneo. Aggiorna Ollama alla versione che supporta la generazione immagini e riprova. " + safe_output)
        image_path = max(image_candidates, key=lambda item: item.stat().st_mtime)
        image_bytes = image_path.read_bytes()
        suffix = image_path.suffix.lower()
        content_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[suffix]
        if not (image_bytes.startswith(b"\x89PNG\r\n\x1a\n") or image_bytes.startswith(b"\xff\xd8\xff") or (image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP")):
            raise RuntimeError("Ollama ha creato un file che non è un'immagine riconosciuta.")
        return _persist_generated_image(prompt, composition, image_bytes, content_type, "Ollama locale", IMAGE_LOCAL_MODEL)


_IMAGE_SIZES = {"square": (1024, 1024), "portrait": (768, 1024), "landscape": (1024, 768)}


def _ollama_text(prompt: str, *, num_predict: int = 400, temperature: float = 0.4, timeout: int = 120,
                 system: str | None = None, json_mode: bool = False) -> str:
    """One-shot completion with the configured local text model (thinking disabled)."""
    model = getattr(RUNTIME, "model_name", "qwen3:1.7b")
    body: dict = {"model": model, "prompt": prompt, "stream": False, "keep_alive": "30m",
                  "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": 8192}}
    if system:
        body["system"] = system
    if json_mode:
        body["format"] = "json"
    if str(model).lower().startswith("qwen3"):
        body["think"] = False
    request = Request(f"{OLLAMA_URL}/api/generate", data=json.dumps(body).encode("utf-8"),
                      headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read(4_000_000).decode("utf-8", errors="replace"))
    except HTTPError as exc:
        raise RuntimeError(f"Il modello locale non ha risposto (HTTP {exc.code}).") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Il modello locale non è disponibile. Verifica che Ollama sia in esecuzione.") from exc
    text = result.get("response", "") if isinstance(result, dict) else ""
    return text if isinstance(text, str) else ""


_PHOTO_STYLE = {
    "fotografia realistica": "photorealistic photograph, natural light, sharp focus, high detail, 35mm lens",
    "ritratto": "professional portrait photograph, soft studio light, shallow depth of field",
    "logo professionale": "clean modern vector logo, flat design, simple geometric shapes, white background",
    "icona": "clean flat icon, simple shapes, centered, plain background",
    "illustrazione": "detailed digital illustration, harmonious colors, soft lighting",
    "poster grafico": "modern graphic poster, bold composition, strong typography space, balanced colors",
    "sfondo": "elegant wallpaper, smooth gradients, high resolution",
}


def enhance_image_prompt(original_request: str, fallback: str) -> str:
    """Rewrite the request as a concise English prompt, which diffusion models follow far better."""
    kind = image_kind(original_request)
    subject = image_subject(original_request)
    style = _PHOTO_STYLE.get(kind, "high quality, detailed, well composed")
    try:
        text = _ollama_text(
            f"Request (any language): {subject}\nStyle: {style}\n\n"
            "Write ONE English prompt of at most 60 words for a text-to-image model. Describe subject, setting, lighting, "
            "colors and composition concretely. Output only the prompt, with no quotes or commentary.",
            num_predict=140, temperature=0.5, timeout=60,
            system="You write precise prompts for text-to-image models.")
        text = " ".join(clean_model_output(text).split()).strip(" \"'")
        if 12 <= len(text) <= 700:
            return text
    except Exception:
        pass
    return f"{subject}, {style}"[:700] if subject else fallback


def generate_svg_illustration(subject: str, composition: str = "square") -> dict:
    """Draw with the local text model: always available, no download, fully private."""
    width, height = _IMAGE_SIZES.get(composition, _IMAGE_SIZES["square"])
    update_progress("generating", "Disegno un'illustrazione vettoriale con il modello locale…")
    prompt = build_svg_prompt(subject, width, height)
    failure = ""
    for attempt in range(2):
        raw = _ollama_text(prompt, num_predict=5000, temperature=0.7 if attempt == 0 else 0.95, timeout=420)
        try:
            svg_bytes = sanitize_svg(extract_svg(raw), width, height)
            return _persist_generated_image(subject, composition, svg_bytes, "image/svg+xml",
                                            "Illustrazione vettoriale locale", getattr(RUNTIME, "model_name", "modello Ollama"))
        except SvgRejected as exc:
            failure = str(exc)
            update_progress("generating", "Il primo disegno non era utilizzabile: riprovo con un'altra variante…")
    raise RuntimeError(f"Il modello locale non è riuscito a disegnare questo soggetto ({failure}). "
                       "Riprova con una descrizione più semplice oppure attiva un generatore fotografico dal pannello Immagini.")


def photo_backend() -> str | None:
    """Name of the best photographic backend currently usable, if any."""
    if ollama_image_model_installed():
        return "ollama"
    if load_image_provider_key():
        return "pollinations"
    if load_image_provider_consent():
        return "aihorde"
    return None


def _generate_image_pollinations(prompt: str, composition: str, key: str) -> dict:
    width, height = _IMAGE_SIZES[composition]
    query = urlencode({"model": IMAGE_GENERATION_MODEL, "width": width, "height": height})
    url = f"https://gen.pollinations.ai/image/{quote(prompt, safe='')}?{query}"
    request = Request(url, headers={"Authorization": f"Bearer {key}", "Accept": "image/png,image/jpeg,image/webp", "User-Agent": "AvoraLocal/1.4.0"})
    try:
        with urlopen(request, timeout=300) as response:
            content_type = (response.headers.get("Content-Type") or "image/jpeg").split(";", 1)[0].strip().lower()
            image_bytes = response.read(MAX_GENERATED_IMAGE_BYTES + 1)
    except HTTPError as exc:
        messages = {401: "La chiave del servizio immagini non è valida.", 402: "Il provider immagini segnala crediti insufficienti. Avora non effettua acquisti.",
                    403: "Pollinations ha negato l'accesso (HTTP 403). Controlla i permessi della chiave.", 429: "Il provider immagini ha raggiunto il limite temporaneo."}
        raise RuntimeError(messages.get(exc.code, f"Il provider immagini ha risposto con errore HTTP {exc.code}.")) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Il provider immagini non è raggiungibile. Controlla Internet.") from exc
    return _persist_generated_image(prompt, composition, image_bytes, content_type, "Pollinations API", IMAGE_GENERATION_MODEL)


def generate_image_local(prompt: str, composition: str = "square", original_request: str | None = None) -> dict:
    """Create an image with the best available backend and always fall back to something usable.

    Order: schema/diagram (local text model) -> local Ollama image model -> Pollinations (user key)
    -> AI Horde (explicit consent) -> local vector illustration. Each stage that fails hands over
    to the next one; only if every stage fails does the caller see an error.
    """
    prompt = " ".join(str(prompt or "").split()).strip()
    if not prompt:
        raise ValueError("Scrivi una descrizione dell'immagine.")
    if len(prompt) > 2000:
        raise ValueError("La descrizione può contenere al massimo 2.000 caratteri.")
    composition = composition if composition in _IMAGE_SIZES else "square"
    request_text = original_request or prompt
    shape = detect_geometric_shape(request_text)
    if shape and not re.search(r"\b(?:foto|realistic\w*|3d|render)\b", request_text, re.IGNORECASE):
        svg = geometric_svg(shape)
        if svg:
            return _persist_generated_image(prompt, composition, svg, "image/svg+xml", "Figura geometrica locale", "Avora")
    if is_diagram_prompt(request_text) or is_diagram_prompt(prompt):
        return generate_diagram_local(prompt, composition)
    subject = image_subject(request_text) or prompt
    errors: list[str] = []
    with _IMAGE_GENERATION_LOCK:
        backend = photo_backend()
        if backend:
            update_progress("generating", "Preparo il prompt per il generatore di immagini…")
            english = enhance_image_prompt(request_text, prompt)
            attempts = []
            if ollama_image_model_installed():
                attempts.append(("Ollama locale", lambda: _generate_image_ollama(english, composition)))
            key = load_image_provider_key()
            if key:
                attempts.append(("Pollinations", lambda: _generate_image_pollinations(english, composition, key)))
            if load_image_provider_consent():
                attempts.append(("AI Horde", lambda: _generate_image_ai_horde(english, composition)))
            for label, runner in attempts:
                try:
                    return runner()
                except (RuntimeError, ImageProviderNotConfigured) as exc:
                    errors.append(f"{label}: {exc}")
                    update_progress("generating", f"{label} non ha completato l'immagine; provo un'alternativa…")
        return generate_svg_illustration(subject, composition)


def detect_web_research_request(message: str) -> bool:
    """Route explicit searches and requests that need fresh online evidence."""
    if detect_image_request(message):
        return False
    return needs_web(classify_intent(message))


def detect_image_request(message: str) -> bool:
    """Recognize a direct image-generation command in Italian or English."""
    return _detect_image_request(message)


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


NEURAL_VOICES = {
    "it-IT-ElsaNeural": "Voce italiana · Elsa",
    "it-IT-IsabellaNeural": "Voce italiana · Isabella",
    "it-IT-DiegoNeural": "Voce italiana · Diego",
    "it-IT-GiuseppeMultilingualNeural": "Voce italiana · Giuseppe",
}
DEFAULT_NEURAL_VOICE = "it-IT-ElsaNeural"


def normalize_tts_voice(value: object) -> str:
    candidate = str(value or DEFAULT_NEURAL_VOICE)
    return candidate if candidate in NEURAL_VOICES else DEFAULT_NEURAL_VOICE


def normalize_tts_rate(value: object) -> tuple[str, float]:
    try:
        multiplier = float(value)
    except (TypeError, ValueError):
        multiplier = 0.95
    multiplier = max(0.80, min(1.15, multiplier))
    pct = round((multiplier - 1.0) * 100)
    return f"{pct:+d}%", multiplier


def _macos_tts(text: str, multiplier: float) -> tuple[bytes, str, str]:
    """Offline fallback using installed macOS voices, outputting a playable WAV."""
    if sys.platform != "darwin":
        raise RuntimeError("Sintesi vocale naturale non disponibile e fallback macOS assente")
    say_bin = "/usr/bin/say"
    if not os.path.exists(say_bin):
        raise RuntimeError("Il comando vocale di macOS non è disponibile")
    rate_wpm = str(max(120, min(220, round(180 * multiplier))))
    with tempfile.TemporaryDirectory(prefix="avora-tts-") as temp_dir:
        folder = Path(temp_dir)
        text_file = folder / "text.txt"
        audio_file = folder / "speech.wav"
        text_file.write_text(text, encoding="utf-8")
        command = [say_bin, "--file-format=WAVE", "-o", str(audio_file), "-r", rate_wpm, "-f", str(text_file)]
        # Prefer an installed Italian system voice, if any.
        try:
            voices = subprocess.run([say_bin, "-v", "?"], capture_output=True, text=True, timeout=5, check=False).stdout
            italian_name = None
            for line in voices.splitlines():
                match = re.match(r"^\s*([A-Za-z][A-Za-z0-9 _-]+?)\s+it[_-]IT\b", line, re.IGNORECASE)
                if match:
                    italian_name = match.group(1).strip()
                    break
            if italian_name:
                command[1:1] = ["-v", italian_name]
        except Exception:
            pass
        subprocess.run(command, capture_output=True, timeout=60, check=True)
        audio = audio_file.read_bytes()
        if len(audio) < 1000:
            raise RuntimeError("macOS non ha generato audio leggibile")
        return audio, "audio/wav", "macos-system"


def synthesize_tts(text: str, voice: object, rate: object) -> tuple[bytes, str, str]:
    """Use natural Edge neural speech when available; fall back to offline macOS TTS."""
    text = str(text or "").strip()
    if not text:
        raise ValueError("Non c'è testo da leggere")
    if len(text) > 10000:
        text = text[:10000]
    selected_voice = normalize_tts_voice(voice)
    rate_text, multiplier = normalize_tts_rate(rate)
    edge_error: Exception | None = None
    try:
        import edge_tts  # optional, installed by the Mac launcher
        with tempfile.TemporaryDirectory(prefix="avora-edge-tts-") as temp_dir:
            audio_file = Path(temp_dir) / "speech.mp3"
            async def save_audio() -> None:
                client = edge_tts.Communicate(text, selected_voice, rate=rate_text)
                await asyncio.wait_for(client.save(str(audio_file)), timeout=40)
            asyncio.run(save_audio())
            audio = audio_file.read_bytes() if audio_file.exists() else b""
            if len(audio) < 800:
                raise RuntimeError("Il servizio vocale non ha restituito un audio valido")
            return audio, "audio/mpeg", "edge-neural-online"
    except Exception as exc:
        edge_error = exc
    try:
        return _macos_tts(text, multiplier)
    except Exception as fallback_error:
        reason = "Servizio di voce neurale non raggiungibile" if edge_error else "Sintesi vocale non disponibile"
        raise RuntimeError(f"{reason}; fallback locale non disponibile ({type(fallback_error).__name__})") from fallback_error


# Preview frame: loaded in a sandboxed iframe without scripts of its own beyond the bundled loader.
# Inline styles are allowed so user HTML looks right; inline scripts, network and forms stay blocked.
PREVIEW_FRAME_CSP = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'self'; "
                     "font-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'self'")
CONTEXT_WINDOW_TOKENS = 8192


def estimate_tokens(messages: list[dict]) -> int:
    text_chars = sum(len(str(m.get("content", ""))) for m in messages)
    image_count = sum(len(m.get("images", [])) for m in messages)
    return max(1, text_chars // 3) + image_count * 768


def image_metadata_from_payload(images: object) -> list[dict]:
    if images is None:
        return []
    if not isinstance(images, list) or len(images) > 4:
        raise ValueError("Puoi allegare al massimo 4 immagini per messaggio.")
    saved = []
    for image in images:
        if not isinstance(image, dict):
            raise ValueError("Allegato immagine non valido.")
        mime = str(image.get("mime", ""))
        if mime not in IMAGE_MIMES:
            raise ValueError("Formato non supportato. Usa PNG, JPEG o WebP.")
        data = image.get("data", "")
        if not isinstance(data, str) or not data:
            raise ValueError("Il contenuto dell'immagine è vuoto.")
        try:
            binary = base64.b64decode(data, validate=True)
        except Exception as exc:
            raise ValueError("Il contenuto dell'immagine non è valido.") from exc
        if len(binary) > MAX_IMAGE_BYTES:
            raise ValueError("Ogni immagine deve essere inferiore a 5 MB.")
        file_id = uuid.uuid4().hex
        storage.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target = storage.UPLOAD_DIR / f"{file_id}{IMAGE_MIMES[mime]}"
        target.write_bytes(binary)
        clean_name = re.sub(r"[^A-Za-z0-9._ -]", "_", str(image.get("name", "immagine")))[:100].strip() or "immagine"
        saved.append({"id": file_id, "name": clean_name, "mime": mime, "size": len(binary), "url": f"/api/files/{file_id}"})
    return saved


def load_images_for_model(messages: list[dict]) -> list[dict]:
    """Load only the two latest image messages into the inference context."""
    with_images = [m for m in messages if m.get("attachments")]
    allowed_ids = {id(m) for m in with_images[-2:]}
    output = []
    for message in messages:
        item = {k: v for k, v in message.items() if k not in {"id", "conversation_id", "created_at", "attachments"}}
        if id(message) in allowed_ids:
            encoded = []
            for attachment in message.get("attachments", [])[:4]:
                path = storage.upload_path(str(attachment.get("id", "")))
                if path and path.stat().st_size <= MAX_IMAGE_BYTES:
                    encoded.append(base64.b64encode(path.read_bytes()).decode("ascii"))
            if encoded:
                item["images"] = encoded
        output.append(item)
    return output


MODEL_PULL_LOCK = threading.Lock()
MODEL_PULL_STATE = {"active": False, "model": "", "phase": "idle", "detail": "", "percent": None, "error": None, "updated_at": None}


def model_pull_snapshot() -> dict:
    with MODEL_PULL_LOCK:
        return dict(MODEL_PULL_STATE)


def _model_pull_worker(model: str) -> None:
    """Download a model through Ollama's HTTP API: no terminal needed, with real progress."""
    def update(**values) -> None:
        with MODEL_PULL_LOCK:
            MODEL_PULL_STATE.update(values, updated_at=time.time())
    try:
        body = json.dumps({"model": model, "stream": True}).encode("utf-8")
        request = Request(f"{OLLAMA_URL}/api/pull", data=body, headers={"Content-Type": "application/json"})
        update(active=True, model=model, phase="downloading", detail="Avvio del download…", percent=0, error=None)
        with urlopen(request, timeout=3600) as response:
            for raw in response:
                try:
                    item = json.loads(raw.decode("utf-8", errors="replace"))
                except ValueError:
                    continue
                if not isinstance(item, dict):
                    continue
                if item.get("error"):
                    raise RuntimeError(str(item["error"])[:300])
                total, done = item.get("total"), item.get("completed")
                percent = int(done * 100 / total) if isinstance(total, int) and total and isinstance(done, int) else None
                status = str(item.get("status", ""))[:80]
                update(phase="downloading", detail=status or "Download in corso…", percent=percent if percent is not None else MODEL_PULL_STATE.get("percent"))
        update(active=False, phase="done", detail=f"{model} installato.", percent=100, error=None)
    except Exception as exc:
        update(active=False, phase="error", detail=str(exc)[:300] or "Download non riuscito.", error=type(exc).__name__)


def start_model_pull(model: object) -> dict:
    from .runtime import MODEL_NAME_RE
    name = str(model or "").strip()
    if not MODEL_NAME_RE.fullmatch(name):
        raise ValueError("Nome modello non valido. Usa un nome come qwen3:4b.")
    if not RUNTIME._ollama_details().get("running"):
        raise ValueError("Ollama non è in esecuzione. Aprilo e riprova.")
    with MODEL_PULL_LOCK:
        if MODEL_PULL_STATE.get("active"):
            return dict(MODEL_PULL_STATE)
        MODEL_PULL_STATE.update(active=True, model=name, phase="starting", detail="Preparazione del download…", percent=0, error=None, updated_at=time.time())
    threading.Thread(target=_model_pull_worker, args=(name,), name="avora-model-pull", daemon=True).start()
    return model_pull_snapshot()


def warm_up_model() -> None:
    """Load the selected model into memory so the first answer does not pay the loading time."""
    if getattr(RUNTIME, "demo", False):
        return
    try:
        for _ in range(30):
            if RUNTIME._ollama_details().get("running"):
                break
            time.sleep(1)
        else:
            return
        details = RUNTIME._ollama_details()
        target = (RUNTIME._text_models(details)[0] if RUNTIME.auto else RUNTIME.model_name)
        if not target or target not in (details.get("installed") or []):
            return
        body = json.dumps({"model": target, "prompt": "", "stream": False, "keep_alive": "30m"}).encode("utf-8")
        request = Request(f"{OLLAMA_URL}/api/generate", data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=180):
            pass
    except Exception:
        pass



class Handler(BaseHTTPRequestHandler):
    server_version = "AvoraLocal/1.4.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[avora] {self.address_string()} - {fmt % args}")

    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8", csp: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", csp or "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: object) -> None:
        self._send(status, json_bytes(value))

    def _read_json(self) -> dict:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Content-Length non valido") from exc
        if size < 0 or size > MAX_BODY:
            raise ValueError("Richiesta troppo grande. Le immagini possono pesare al massimo 5 MB ciascuna.")
        raw = self.rfile.read(size) if size else b"{}"
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("Il corpo deve essere un oggetto JSON")
        return parsed

    def do_HEAD(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            file_path = ASSETS / "index.html"
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return
        if path.startswith("/assets/"):
            name = path.removeprefix("/assets/")
            if "/" not in name and "\\" not in name and not name.startswith("."):
                file_path = ASSETS / name
                if file_path.is_file():
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
                    self.send_header("Content-Length", str(file_path.stat().st_size))
                    self.end_headers()
                    return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path in {"/", "/index.html"}:
                return self._send(200, (ASSETS / "index.html").read_bytes(), "text/html; charset=utf-8")
            if path == "/api/health":
                return self._json(200, {"ok": True, "name": "Avora", "version": "1.4.0"})
            if path == "/api/status":
                return self._json(200, RUNTIME.status())
            if path == "/api/personas":
                from .personas import persona_list
                return self._json(200, {"personas": persona_list()})
            if path == "/api/usage":
                return self._json(200, {"usage": storage.usage_snapshot(), "events": storage.recent_usage_events(10)})
            if path == "/api/progress":
                return self._json(200, {"progress": progress_snapshot()})
            if path == "/api/images":
                return self._json(200, {**list_image_gallery(), "generator": image_generation_status()})
            if path == "/api/models/pull":
                return self._json(200, {"pull": model_pull_snapshot()})
            if path == "/api/images/install-status":
                return self._json(200, {"install": image_install_snapshot(), "generator": image_generation_status()})
            uploaded_gallery_match = re.fullmatch(r"/api/gallery/uploads/([a-f0-9]{32})", path)
            if uploaded_gallery_match:
                image_path = _gallery_upload_path(uploaded_gallery_match.group(1))
                if not image_path:
                    return self._json(404, {"error": "Immagine caricata non trovata"})
                mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
                return self._send(200, image_path.read_bytes(), mime)
            generated_match = re.fullmatch(r"/api/generated/([a-f0-9]{32})", path)
            if generated_match:
                image_path = _generated_path(generated_match.group(1))
                if not image_path:
                    return self._json(404, {"error": "Immagine generata non trovata"})
                mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
                return self._send(200, image_path.read_bytes(), mime)
            if path == "/api/conversations":
                return self._json(200, {"conversations": storage.list_conversations()})
            file_match = re.fullmatch(r"/api/files/([a-f0-9]{32})", path)
            if file_match:
                file_path = storage.upload_path(file_match.group(1))
                if not file_path:
                    return self._json(404, {"error": "Immagine non trovata"})
                mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                return self._send(200, file_path.read_bytes(), mime)
            match = re.fullmatch(r"/api/conversations/([a-f0-9]{32})", path)
            if match:
                conversation_id = match.group(1)
                conversation = storage.get_conversation(conversation_id)
                if not conversation:
                    return self._json(404, {"error": "Conversazione non trovata"})
                return self._json(200, {"conversation": conversation, "messages": storage.get_messages(conversation_id)})
            if path.startswith("/assets/"):
                name = path.removeprefix("/assets/")
                if "/" in name or "\\" in name or name.startswith("."):
                    return self._json(404, {"error": "Risorsa non trovata"})
                file_path = ASSETS / name
                if not file_path.is_file():
                    return self._json(404, {"error": "Risorsa non trovata"})
                mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                if mime in {"text/css", "application/javascript"}:
                    mime += "; charset=utf-8"
                csp = PREVIEW_FRAME_CSP if name == "artifact-frame.html" else None
                return self._send(200, file_path.read_bytes(), mime, csp)
            return self._json(404, {"error": "Endpoint non trovato"})
        except Exception as exc:
            return self._json(500, {"error": f"Errore interno: {type(exc).__name__}"})

    def do_POST(self) -> None:
        self._stream_started = False
        try:
            payload = self._read_json()
            path = urlparse(self.path).path
            if path == "/api/conversations":
                title = str(payload.get("title", "Nuova conversazione"))[:90]
                return self._json(201, {"conversation": storage.create_conversation(title)})
            if path == "/api/settings/auto":
                enabled = payload.get("auto")
                if not isinstance(enabled, bool):
                    return self._json(400, {"error": "Valore non valido."})
                status = RUNTIME.set_auto(enabled)
                threading.Thread(target=warm_up_model, daemon=True).start()
                return self._json(200, {"status": status})
            if path == "/api/settings/model":
                model_name = payload.get("model")
                if not isinstance(model_name, str):
                    return self._json(400, {"error": "Indica il nome del modello, ad esempio qwen3:1.7b"})
                status = RUNTIME.set_model(model_name)
                threading.Thread(target=warm_up_model, daemon=True).start()
                return self._json(200, {"status": status})
            if path == "/api/settings/vision-model":
                model_name = payload.get("model")
                if not isinstance(model_name, str):
                    return self._json(400, {"error": "Indica il modello per le immagini, ad esempio qwen3-vl:2b"})
                return self._json(200, {"status": RUNTIME.set_vision_model(model_name)})
            if path == "/api/settings/usage":
                limit = payload.get("token_limit")
                if not isinstance(limit, int):
                    return self._json(400, {"error": "Indica un limite token valido"})
                return self._json(200, {"usage": storage.set_usage_limit(limit)})
            if path == "/api/settings/plan":
                plan = payload.get("plan")
                if not isinstance(plan, str):
                    return self._json(400, {"error": "Scegli un livello di utilizzo valido"})
                return self._json(200, {"usage": storage.set_usage_plan(plan)})
            if path == "/api/tts":
                text = payload.get("text", "")
                if not isinstance(text, str) or not text.strip():
                    return self._json(400, {"error": "Indica il testo da leggere"})
                if len(text) > 10000:
                    return self._json(413, {"error": "Testo troppo lungo per la sintesi vocale"})
                try:
                    audio, mime, provider = synthesize_tts(text, payload.get("voice"), payload.get("rate", 0.95))
                except Exception as exc:
                    return self._json(503, {"error": str(exc) or "Sintesi vocale non disponibile"})
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(audio)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Avora-TTS-Provider", provider)
                self.end_headers()
                self.wfile.write(audio)
                return
            if path == "/api/search":
                query = payload.get("query", "")
                if not isinstance(query, str) or not query.strip():
                    return self._json(400, {"error": "Scrivi cosa vuoi cercare sul web."})
                if len(query) > 400:
                    return self._json(413, {"error": "La ricerca può contenere al massimo 400 caratteri."})
                try:
                    from .websearch import WebSearchUnavailable, search_web
                    results = search_web(query, limit=8)
                except WebSearchUnavailable as exc:
                    return self._json(502, {"error": str(exc), "code": "web_search_unavailable"})
                except Exception as exc:
                    return self._json(502, {"error": f"Ricerca non riuscita ({type(exc).__name__}). Controlla la connessione Internet e riprova.", "code": "web_search_error"})
                return self._json(200, {"query": query.strip(), "results": results, "count": len(results)})
            if path == "/api/images/install-local":
                result = start_image_model_install()
                status_code = 202 if result.get("active") else (200 if result.get("installed") else 409)
                return self._json(status_code, {"install": result, "generator": image_generation_status()})
            if path == "/api/images/upload":
                try:
                    image = save_gallery_upload(payload.get("filename"), payload.get("mime"), payload.get("data"))
                except ValueError as exc:
                    return self._json(400, {"error": str(exc)})
                return self._json(201, {"image": image})
            if path == "/api/settings/image-consent":
                consent = payload.get("consent")
                if not isinstance(consent, bool):
                    return self._json(400, {"error": "La conferma deve essere booleana."})
                configured = save_image_provider_consent(consent)
                return self._json(200, {"consent": configured, "generator": image_generation_status()})
            if path == "/api/settings/image-provider":
                key = payload.get("api_key", "")
                if not isinstance(key, str):
                    return self._json(400, {"error": "Chiave del provider non valida."})
                try:
                    configured = save_image_provider_key(key)
                except ValueError as exc:
                    return self._json(400, {"error": str(exc)})
                return self._json(200, {"configured": configured, "generator": image_generation_status()})
            if path == "/api/images/generate-chat":
                message = payload.get("message", "")
                prompt = payload.get("prompt", "")
                composition = payload.get("composition", "square")
                conversation_id = payload.get("conversation_id")
                if not isinstance(message, str) or not message.strip():
                    return self._json(400, {"error": "Scrivi cosa vuoi vedere nell'immagine."})
                if len(message) > 12000 or (isinstance(prompt, str) and len(prompt) > 2000):
                    return self._json(413, {"error": "La descrizione è troppo lunga."})
                try:
                    begin_progress(images_count=0)
                    update_progress("generating", "Creo l'immagine richiesta…")
                    result = generate_image_chat_turn(message, prompt if isinstance(prompt, str) else "", str(composition), conversation_id if isinstance(conversation_id, str) else None)
                except ImageProviderNotConfigured as exc:
                    finish_progress("error", "Il generatore immagini richiede una configurazione iniziale.")
                    return self._json(409, {"error": str(exc), "code": "image_provider_not_configured", "generator": image_generation_status()})
                except (ValueError, RuntimeError) as exc:
                    finish_progress("error", "La generazione dell'immagine non è riuscita.")
                    return self._json(409, {"error": str(exc), "code": "image_generation_failed", "generator": image_generation_status()})
                finish_progress("done", "Immagine creata e aggiunta alla conversazione.")
                return self._json(201, result)
            if path == "/api/images/generate":
                prompt = payload.get("prompt", "")
                composition = payload.get("composition", "square")
                if not isinstance(prompt, str):
                    return self._json(400, {"error": "Descrizione immagine non valida."})
                try:
                    generated = generate_image_local(prompt, str(composition))
                except ValueError as exc:
                    return self._json(400, {"error": str(exc)})
                except RuntimeError as exc:
                    return self._json(409, {"error": str(exc), "generator": image_generation_status()})
                return self._json(201, {"image": generated})
            truncate_match = re.fullmatch(r"/api/conversations/([a-f0-9]{32})/truncate", path)
            if truncate_match:
                try:
                    keep = int(payload.get("keep"))
                except (TypeError, ValueError):
                    return self._json(400, {"error": "Numero di messaggi non valido"})
                if not storage.get_conversation(truncate_match.group(1)):
                    return self._json(404, {"error": "Conversazione non trovata"})
                removed = storage.truncate_messages(truncate_match.group(1), keep)
                return self._json(200, {"removed": removed, "messages": storage.get_messages(truncate_match.group(1))})
            feedback_match = re.fullmatch(r"/api/messages/(\d{1,12})/feedback", path)
            if feedback_match:
                try:
                    ok = storage.set_feedback(int(feedback_match.group(1)), str(payload.get("value", "")))
                except ValueError as exc:
                    return self._json(400, {"error": str(exc)})
                return self._json(200 if ok else 404, {"ok": ok})
            compact_match = re.fullmatch(r"/api/conversations/([a-f0-9]{32})/compact", path)
            if compact_match:
                try:
                    created = compact_conversation(compact_match.group(1))
                except RuntimeError as exc:
                    return self._json(503, {"error": str(exc)})
                return self._json(201, {"conversation": created, "messages": storage.get_messages(created["id"])})
            if path == "/api/models/pull":
                result = start_model_pull(payload.get("model"))
                return self._json(202 if result.get("active") else 200, {"pull": result})
            if path == "/api/chat/stream":
                return self._handle_chat(payload, stream=True)
            if path == "/api/chat":
                return self._handle_chat(payload)
            return self._json(404, {"error": "Endpoint non trovato"})
        except (BrokenPipeError, ConnectionResetError):
            return None
        except ValueError as exc:
            if self._stream_started:
                return None
            return self._json(400, {"error": str(exc)})
        except KeyError as exc:
            if self._stream_started:
                return None
            return self._json(404, {"error": str(exc).strip("'")})
        except Exception as exc:
            if self._stream_started:
                return None
            return self._json(500, {"error": f"Errore interno: {type(exc).__name__}"})

    def _handle_chat(self, payload: dict, stream: bool = False) -> None:
        message = payload.get("message", "")
        images_payload = payload.get("images", [])
        if isinstance(message, str) and not message.strip() and images_payload:
            message = "Analizza l'immagine allegata."
        think = bool(payload.get("think"))
        request_intent = classify_intent(message)
        deep_research = bool(payload.get("deep_research")) or needs_web(request_intent)
        search_query = build_search_query(message, request_intent) if deep_research else ""
        if not isinstance(message, str) or (not message.strip() and not images_payload):
            return self._json(400, {"error": "Scrivi un messaggio o allega un'immagine."})
        if len(message) > 12000:
            return self._json(413, {"error": "Messaggio troppo lungo (massimo 12.000 caratteri)"})
        if deep_research and not message.strip():
            return self._json(400, {"error": "Scrivi una domanda per avviare la ricerca web."})
        # Route plain-language image creation requests even if a frontend detector misses them.
        if not images_payload and detect_image_request(message):
            try:
                begin_progress(images_count=0)
                result = generate_image_chat_turn(message, "", normalize_image_prompt(message)[1],
                                                  payload.get("conversation_id") if isinstance(payload.get("conversation_id"), str) else None)
                finish_progress("done", "Immagine creata e salvata.", images_count=1)
                return self._json(201, result)
            except ImageProviderNotConfigured as exc:
                finish_progress("error", "Serve una conferma iniziale per usare il generatore gratuito.")
                return self._json(409, {"error": str(exc), "code": "image_provider_not_configured", "generator": image_generation_status()})
            except (ValueError, RuntimeError) as exc:
                finish_progress("error", "La generazione dell'immagine non è riuscita.")
                return self._json(502, {"error": str(exc), "code": "image_generation_failed", "generator": image_generation_status()})
        begin_progress(images_count=len(images_payload) if isinstance(images_payload, list) else 0, deep_research=deep_research)
        usage = storage.usage_snapshot()
        if usage["remaining_tokens"] <= 64:
            finish_progress("limited", "Limite token raggiunto; attesa del reset automatico.")
            reset_local = datetime.fromtimestamp(time.time() + usage["seconds_until_reset"]).strftime("%H:%M")
            mins = max(1, (usage["seconds_until_reset"] + 59) // 60)
            return self._json(429, {"error": f"Hai raggiunto il limite locale per questa finestra di 3 ore. Potrai riprendere alle {reset_local} (ora locale, tra circa {mins} minuti).", "code": "usage_limit", "usage": usage})
        # Obvious arithmetic expressions can be answered exactly without waiting for the LLM.
        # More complex maths still goes to the configured model with a dedicated instruction.
        if not deep_research and not images_payload:
            from .math_tools import solve_simple_arithmetic
            local_math_reply = solve_simple_arithmetic(message)
            if local_math_reply is not None:
                requested_id = payload.get("conversation_id")
                existing = storage.get_conversation(requested_id) if isinstance(requested_id, str) and re.fullmatch(r"[a-f0-9]{32}", requested_id) else None
                conversation = existing or storage.create_conversation((" ".join(message.split())[:54] or "Calcolo") )
                conversation_id = conversation["id"]
                user_message = storage.add_message(conversation_id, "user", message.strip())
                assistant_message = storage.add_message(conversation_id, "assistant", local_math_reply)
                prompt_tokens = max(1, len(message) // 3)
                completion_tokens = max(1, len(local_math_reply) // 3)
                usage = storage.charge_usage(prompt_tokens, completion_tokens, "local-math", conversation_id)
                finish_progress("done", "Calcolo aritmetico verificato localmente.",
                                generated_tokens=completion_tokens, partial_text=local_math_reply)
                return self._json(200, {
                    "conversation_id": conversation_id, "conversation": storage.get_conversation(conversation_id),
                    "user_message": user_message, "assistant_message": assistant_message, "mode": "local-math",
                    "usage": usage, "metrics": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens, "model": "Calcolo locale", "thinking_used": False},
                    "research_used": False, "sources_count": 0,
                })
        # Readiness errors are transport errors, never assistant messages in history.
        try:
            runtime_status = RUNTIME.status()
        except Exception:
            runtime_status = {"model_loaded": False, "engine": "unknown"}
        if not runtime_status.get("model_loaded"):
            detail = runtime_status.get("description") or "Apri Ollama e verifica il modello selezionato nelle impostazioni."
            finish_progress("error", "Il motore non è pronto; nessun messaggio di stato è stato salvato.")
            return self._json(503, {"error": detail, "code": "model_not_ready"})
        if images_payload and runtime_status.get("engine") == "ollama" and not runtime_status.get("vision_model_loaded"):
            vision_model = str(runtime_status.get("vision_model") or "qwen3-vl:2b")
            finish_progress("error", "Il modello visivo non è installato.")
            return self._json(503, {"error": f"Per analizzare immagini serve il modello visivo {vision_model}. Puoi installarlo con un clic da Impostazioni, sezione Modello.", "code": "vision_model_missing"})
        requested_id = payload.get("conversation_id")
        conversation = storage.get_conversation(requested_id) if isinstance(requested_id, str) and re.fullmatch(r"[a-f0-9]{32}", requested_id) else None
        conversation_id = conversation["id"] if conversation else None
        attachments: list[dict] = []
        try:
            attachments = image_metadata_from_payload(images_payload)
            prior_history = storage.get_messages(conversation_id, limit=24) if conversation_id else []
            user_item = {"role": "user", "content": message.strip(), "attachments": attachments,
                         "created_at": datetime.now().astimezone().isoformat(timespec="seconds")}
            model_history = load_images_for_model(prior_history + [user_item])
            budget_history = [dict(item) for item in model_history[-24:]]
            context_estimate = estimate_tokens(RUNTIME._select_history(budget_history, deep_research))
            remaining = usage["remaining_tokens"]
            if context_estimate + 64 >= remaining:
                finish_progress("limited", "Contesto troppo grande per il budget token rimasto.")
                for attachment in attachments:
                    storage.delete_upload(attachment.get("id", ""))
                return self._json(429, {"error": "La conversazione è troppo lunga per il budget token rimasto. Crea una nuova chat o attendi il reset automatico.", "code": "usage_limit", "usage": usage})
            voice_mode = bool(payload.get("voice_mode"))
            agent_mode = bool(payload.get("agent")) and not voice_mode
            persona_id = str(payload.get("persona", "general"))[:24]
            max_tokens = max(256, min(11000 if think else 9500, remaining - context_estimate))

            def emit_event(event: dict) -> None:
                self.wfile.write(json_bytes(event) + b"\n")
                self.wfile.flush()

            def begin_stream() -> None:
                if not self._stream_started:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Accel-Buffering", "no")
                    self.end_headers()
                    self._stream_started = True

            def delta_callback(text: str) -> None:
                if not stream:
                    return
                begin_stream()
                visible = strip_emoji(text)
                if visible:
                    emit_event({"type": "delta", "text": visible})

            def tool_callback(event: dict) -> None:
                if not stream:
                    return
                begin_stream()
                slim = {k: v for k, v in event.items() if k != "images"}
                emit_event(slim)

            def respond(status: int, body: dict) -> None:
                if stream and (self._stream_started or status < 400):
                    begin_stream()
                    try:
                        emit_event({"type": "error" if status >= 400 else "done", "status": status, **body})
                    except OSError:
                        pass
                    return
                self._json(status, body)

            reply, mode, metrics = RUNTIME.reply_with_metadata(budget_history, {
                "think": think, "deep_research": deep_research, "images": bool(attachments),
                "intent": request_intent, "search_query": search_query,
                "math_request": bool(re.search(r"\b(?:quanto fa|calcola|calcolami|risolvi|equazione|disequazione|derivata|integrale|percentuale|teorema|geometria|algebra|matematica|semplifica|fattorizza|sistema di equazioni|problema di fisica|dimostra che)\b", message, re.I)),
                "custom_instructions": str(payload.get("custom_instructions", ""))[:3000],
                "response_style": str(payload.get("response_style", "balanced"))[:24],
                "voice_mode": voice_mode, "delta_callback": delta_callback if stream else None,
                "agent": agent_mode, "tool_callback": tool_callback if (stream and agent_mode) else None,
                "persona": persona_id, "persona_prompt": str(payload.get("persona_prompt", ""))[:2000],
                "progress_callback": lambda phase, detail, **extra: update_progress(phase, detail, **extra),
            }, max_tokens=max_tokens)
            successful_modes = {"demo", "ollama", "ollama-vision", "ollama-think", "ollama-research", "clara-instruct"}
            if mode not in successful_modes:
                for attachment in attachments:
                    storage.delete_upload(attachment.get("id", ""))
                finish_progress("error", "La richiesta non è riuscita; nessun avviso è stato salvato come risposta.")
                return respond(503, {"error": reply or "Il modello non ha potuto generare una risposta. Controlla Impostazioni → Modello.", "code": "generation_failed", "mode": mode})
            if conversation is None:
                first_line = " ".join(message.strip().split()) or "Analisi immagine"
                title = first_line[:54] + ("…" if len(first_line) > 54 else "")
                conversation = storage.create_conversation(title or "Nuova conversazione")
                conversation_id = conversation["id"]
            user_message = storage.add_message(conversation_id, "user", message.strip(), attachments)
            assistant_attachments = _tool_attachments(metrics)
            assistant_message = storage.add_message(conversation_id, "assistant", reply, assistant_attachments)
            usage = storage.charge_usage(metrics.get("prompt_tokens", 0), metrics.get("completion_tokens", 0), mode, conversation_id)
            finish_progress("done", "Risposta generata.", generated_tokens=metrics.get("completion_tokens", 0),
                            partial_text=reply, sources_count=metrics.get("sources_count", len(metrics.get("web_sources", []))))
            return respond(200, {
                "conversation_id": conversation_id, "conversation": storage.get_conversation(conversation_id),
                "user_message": user_message, "assistant_message": assistant_message, "mode": mode, "usage": usage,
                "metrics": {"prompt_tokens": metrics.get("prompt_tokens", 0), "completion_tokens": metrics.get("completion_tokens", 0),
                            "total_tokens": metrics.get("total_tokens", 0), "model": metrics.get("model", RUNTIME.model_name),
                            "thinking_used": metrics.get("thinking_used", False)},
                "research_used": deep_research, "sources_count": len(metrics.get("web_sources", [])),
                "intent": request_intent,
                "context": {"used_tokens": int(metrics.get("prompt_tokens", 0)) + int(metrics.get("completion_tokens", 0)), "window_tokens": CONTEXT_WINDOW_TOKENS},
            })
        except Exception:
            finish_progress("error", "La richiesta non è stata completata.")
            for attachment in attachments:
                storage.delete_upload(attachment.get("id", ""))
            raise

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/conversations/([a-f0-9]{32})", path)
        if not match:
            return self._json(404, {"error": "Endpoint non trovato"})
        try:
            payload = self._read_json()
            title = payload.get("title")
            if not isinstance(title, str) or not title.strip():
                return self._json(400, {"error": "Titolo non valido"})
            ok = storage.rename_conversation(match.group(1), title)
            if not ok:
                return self._json(404, {"error": "Conversazione non trovata"})
            return self._json(200, {"conversation": storage.get_conversation(match.group(1))})
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        except Exception as exc:
            return self._json(500, {"error": f"Errore interno: {type(exc).__name__}"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/conversations/([a-f0-9]{32})", path)
        if not match:
            return self._json(404, {"error": "Endpoint non trovato"})
        try:
            ok = storage.delete_conversation(match.group(1))
            if not ok:
                return self._json(404, {"error": "Conversazione non trovata"})
            return self._json(200, {"deleted": True})
        except Exception as exc:
            return self._json(500, {"error": f"Errore interno: {type(exc).__name__}"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Avvia Avora solo sul computer locale")
    parser.add_argument("--host", default="127.0.0.1", help="Indirizzo di bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Porta HTTP (default: 8765)")
    parser.add_argument("--demo", action="store_true", help="Modalità demo: risposte di esempio senza modello")
    parser.add_argument("--no-browser", action="store_true", help="Non aprire il browser automaticamente")
    args = parser.parse_args()
    if args.demo:
        RUNTIME.demo = True
    storage.init_db()
    threading.Thread(target=warm_up_model, name="avora-warmup", daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("\n  Avora — locale e privata")
    print(f"  Apri http://127.0.0.1:{args.port}")
    print("  Modalità demo attiva" if RUNTIME.demo else "  Modello locale · ricerca web solo quando serve", "· Ctrl+C per uscire\n")
    if not args.no_browser:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAvora arrestata.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
