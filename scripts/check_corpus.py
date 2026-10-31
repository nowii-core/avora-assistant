#!/usr/bin/env python3
"""Audit corpus size, duplicates, encoding, and metadata before training."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clara_core.corpus import discover_files, iter_documents


def main():
    p = argparse.ArgumentParser(description="Controlla corpus e duplicati prima dell'addestramento")
    p.add_argument("--input", type=Path, default=ROOT / "data" / "corpus")
    p.add_argument("--out", type=Path, default=ROOT / "data" / "processed" / "corpus-report.json")
    args = p.parse_args()
    files = discover_files(args.input); seen = set(); duplicate_docs = 0; docs = chars = 0; total_bytes = 0
    per_file = []
    for path in files:
        try: size = path.stat().st_size
        except OSError: size = 0
        total_bytes += size
        per_file.append({"path": str(path), "bytes": size})
    for text, source in iter_documents(args.input):
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key in seen: duplicate_docs += 1
        else: seen.add(key)
        docs += 1; chars += len(text)
    result = {
        "input": str(args.input.expanduser().resolve()), "files": len(files), "documents": docs,
        "unique_documents": len(seen), "duplicate_documents": duplicate_docs,
        "characters": chars, "file_bytes": total_bytes,
        "estimated_utf8_mb": round(total_bytes / 1_000_000, 3), "per_file": per_file,
        "training_ready": docs > 0 and chars >= 100_000,
        "note": "La soglia è indicativa; 100.000 caratteri non bastano per creare un assistente generalista.",
    }
    out = args.out.expanduser().resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Report salvato: {out}")

if __name__ == "__main__": main()
