#!/usr/bin/env python3
"""Train Avora's own byte-level BPE tokenizer from local text."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clara_core.corpus import iter_documents
from clara_core.tokenizer import train_bpe_from_iterator


def main() -> None:
    parser = argparse.ArgumentParser(description="Addestra il tokenizer BPE di Avora da zero")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "corpus")
    parser.add_argument("--out", type=Path, default=ROOT / "checkpoints" / "tokenizer.json")
    parser.add_argument("--vocab-size", type=int, default=4096)
    parser.add_argument("--min-frequency", type=int, default=2)
    args = parser.parse_args()
    args.input = args.input.expanduser().resolve()
    args.out = args.out.expanduser().resolve()
    docs_count = 0
    chars = 0
    source_iter = iter(iter_documents(args.input))
    first = next(source_iter, None)
    if first is None:
        raise SystemExit(f"Nessun testo leggibile trovato in {args.input}. Inserisci dati autorizzati o usa scripts/fetch_wikipedia.py.")
    def stream():
        nonlocal docs_count, chars
        for text, _source in [first]:
            docs_count += 1; chars += len(text); yield text
        for text, _source in source_iter:
            docs_count += 1; chars += len(text); yield text
    ids = train_bpe_from_iterator(stream(), args.out, args.vocab_size, args.min_frequency)
    manifest = {
        "kind": "byte-level-bpe",
        "trained_from_scratch": True,
        "pretrained_model_used": False,
        "documents": docs_count,
        "characters": chars,
        "requested_vocab_size": args.vocab_size,
        "actual_vocab_size": None,
        "special_token_ids": ids,
        "tokenizer_path": str(args.out),
        "warning": "Un tokenizer ben formato non sostituisce il pre-training del modello linguistico.",
    }
    try:
        from clara_core.tokenizer import load_tokenizer
        tok = load_tokenizer(args.out)
        manifest["actual_vocab_size"] = tok.get_vocab_size(with_added_tokens=True)
    except Exception:
        pass
    args.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tokenizer salvato: {args.out}")
    print(f"Documenti: {docs_count:,} | caratteri: {chars:,} | vocab: {manifest['actual_vocab_size']}")
    print("I token sono stati imparati dal tuo corpus; non è stato caricato alcun modello preaddestrato.")

if __name__ == "__main__":
    main()
