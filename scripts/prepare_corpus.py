#!/usr/bin/env python3
"""Consolida file testuali locali in un corpus UTF-8, senza scaricare dati."""
from __future__ import annotations
import argparse
from pathlib import Path

EXTENSIONS = {".txt", ".md"}

def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara corpus da file locali autorizzati")
    parser.add_argument("source", type=Path, help="File o cartella contenente .txt/.md")
    parser.add_argument("--out", type=Path, default=Path("data/corpus/prepared.txt"))
    args = parser.parse_args()
    paths = [args.source] if args.source.is_file() else sorted(p for p in args.source.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
    chunks = []
    for path in paths:
        if path.suffix.lower() not in EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            chunks.append(f"\n\n## {path.name}\n{text}\n")
    if not chunks:
        raise SystemExit("Nessun file .txt o .md leggibile trovato.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(chunks), encoding="utf-8")
    print(f"Creato {args.out}: {len(chunks)} file, {sum(map(len, chunks)):,} caratteri")
    print("Usa solo testi che hai il diritto di utilizzare per l'addestramento.")

if __name__ == "__main__":
    main()
