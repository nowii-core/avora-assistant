#!/usr/bin/env python3
"""Optional explicit downloader for a small starter corpus from Wikipedia.

The chat app itself does not access the internet. This script runs only when the
user explicitly calls it; every record stores title/source/license metadata.
"""
from __future__ import annotations
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def request_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "AvoraAIResearch/0.3 (local language-model dataset builder; contact: github.com/nowii-core)"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    p = argparse.ArgumentParser(description="Scarica un piccolo corpus Wikipedia con fonti e licenza registrate")
    p.add_argument("--lang", default="it", help="Codice lingua Wikipedia: it, en, es, fr...")
    p.add_argument("--pages", type=int, default=200, help="Numero massimo di pagine da raccogliere (parti con 200)")
    p.add_argument("--chars-per-page", type=int, default=5000)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--delay", type=float, default=0.3, help="Pausa fra richieste")
    args = p.parse_args()
    if not args.lang.isalpha() or not (2 <= len(args.lang) <= 12): p.error("Codice lingua non valido")
    if args.pages < 1 or args.pages > 10000: p.error("pages deve essere fra 1 e 10000")
    if args.chars_per_page < 500 or args.chars_per_page > 20000: p.error("chars-per-page deve essere fra 500 e 20000")
    out = (args.out.expanduser().resolve() if args.out else ROOT / "data" / "corpus" / f"wikipedia-{args.lang}.jsonl").resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    api = f"https://{args.lang}.wikipedia.org/w/api.php"
    seen: set[str] = set(); count = 0
    if out.exists():
        try:
            with out.open("r", encoding="utf-8", errors="replace") as old_file:
                for line in old_file:
                    try:
                        row = json.loads(line)
                        if row.get("title"): seen.add(str(row["title"]))
                    except json.JSONDecodeError: pass
        except OSError: pass
    mode = "a" if out.exists() else "w"
    with out.open(mode, encoding="utf-8") as handle:
        while count < args.pages:
            limit = min(10, args.pages - count)
            params = {
                "action": "query", "format": "json", "formatversion": 2,
                "generator": "random", "grnnamespace": 0, "grnlimit": limit,
                "prop": "extracts", "explaintext": 1, "exchars": args.chars_per_page,
            }
            try:
                data = request_json(api + "?" + urlencode(params))
            except Exception as exc:
                print(f"Errore di rete/API: {type(exc).__name__}: {exc}")
                print("Il downloader è facoltativo. Riprova più tardi o importa file di testo autorizzati.")
                break
            pages = data.get("query", {}).get("pages", [])
            if isinstance(pages, dict): pages = list(pages.values())
            for page in pages:
                title = str(page.get("title", "")).strip()
                text = str(page.get("extract", "")).strip()
                page_id = page.get("pageid")
                if not title or len(text) < 300 or title in seen: continue
                seen.add(title)
                url = f"https://{args.lang}.wikipedia.org/?curid={page_id}"
                item = {
                    "text": f"Titolo: {title}\n\n{text}",
                    "title": title, "source_url": url, "history_url": url + "&action=history",
                    "source": f"Wikipedia ({args.lang})",
                    "license_notice": "Il testo Wikipedia è generalmente CC BY-SA 4.0 e/o GFDL; verificare il footer e le eccezioni della singola pagina. Attribuzione e obblighi ShareAlike possono applicarsi.",
                    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                    "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "modifications": "Testo estratto tramite MediaWiki API; formattazione e parte dell'estratto possono essere state ridotte.",
                }
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
                if count % 25 == 0: print(f"Raccolte {count}/{args.pages} pagine")
            handle.flush()
            if args.delay > 0: time.sleep(args.delay)
    print(f"Corpus scritto/aggiornato: {out} | nuove pagine: {count}")
    print("Nota: Wikipedia è solo un piccolo punto di partenza, non un dataset sufficiente per un LLM competitivo.")

if __name__ == "__main__": main()
