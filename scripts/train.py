#!/usr/bin/env python3
"""Pre-train Avora Transformer from random weights on UTF-8 text."""
from __future__ import annotations
import argparse
import array
import hashlib
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clara_core.corpus import iter_documents
from clara_core.tokenizer import load_tokenizer, special_token_ids, train_bpe_from_iterator


def choose_device(torch, choice: str) -> str:
    if choice != "auto":
        if choice == "cuda" and not torch.cuda.is_available():
            raise SystemExit("CUDA non disponibile; prova --device auto o --device cpu")
        if choice == "mps" and not (getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()):
            raise SystemExit("MPS non disponibile; prova --device auto o --device cpu")
        return choice
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def make_tokens(input_path: Path, tokenizer, special: dict[str, int]):
    token_ids = array.array("I")
    digest = hashlib.sha256()
    file_sources: list[str] = []
    docs = chars = 0
    for text, source in iter_documents(input_path):
        if len(text) < 20:
            continue
        digest.update(text.encode("utf-8")); digest.update(b"\n\n")
        token_ids.append(special["<|bos|>"])
        token_ids.extend(tokenizer.encode(text, add_special_tokens=False).ids)
        token_ids.append(special["<|eos|>"])
        docs += 1; chars += len(text)
        if len(file_sources) < 5000:
            file_sources.append(source)
    if not docs:
        raise SystemExit(f"Nessun testo utile trovato in {input_path}. Inserisci testi .txt/.md/.jsonl autorizzati.")
    if len(token_ids) < 100:
        raise SystemExit(f"Corpus molto piccolo ({len(token_ids)} token). Aggiungi altri testi prima del training.")
    return token_ids, digest.hexdigest(), file_sources, docs, chars


def sample_batch(np, torch, data, batch_size: int, block_size: int, device: str):
    max_start = len(data) - block_size - 1
    if max_start < 1:
        raise ValueError(f"Servono almeno {block_size + 2} token nella partizione; ne sono presenti {len(data)}")
    starts = np.random.randint(0, max_start + 1, size=batch_size)
    x = np.stack([data[int(s):int(s) + block_size] for s in starts]).astype(np.int64, copy=False)
    y = np.stack([data[int(s) + 1:int(s) + block_size + 1] for s in starts]).astype(np.int64, copy=False)
    return torch.from_numpy(x).to(device), torch.from_numpy(y).to(device)


def main() -> None:
    p = argparse.ArgumentParser(description="Pre-training autoregressivo di Avora da pesi casuali")
    p.add_argument("--input", type=Path, default=ROOT / "data" / "corpus")
    p.add_argument("--tokenizer", type=Path, default=ROOT / "checkpoints" / "tokenizer.json")
    p.add_argument("--train-tokenizer", action="store_true", help="Riaddestra il tokenizer; richiede di rifare anche il modello da zero")
    p.add_argument("--vocab-size", type=int, default=4096)
    p.add_argument("--steps", type=int, default=3000, help="Numero di passi aggiuntivi, oppure passi totali senza --resume")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--block-size", type=int, default=256)
    p.add_argument("--n-embd", type=int, default=128)
    p.add_argument("--n-head", type=int, default=4)
    p.add_argument("--n-layer", type=int, default=4)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--learning-rate", type=float, default=3e-4)
    p.add_argument("--min-learning-rate", type=float, default=3e-5)
    p.add_argument("--warmup-steps", type=int, default=100)
    p.add_argument("--eval-interval", type=int, default=100)
    p.add_argument("--eval-batches", type=int, default=8)
    p.add_argument("--save-every", type=int, default=500)
    p.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--resume", type=Path, default=None)
    p.add_argument("--out", type=Path, default=ROOT / "checkpoints" / "avora-pretrain.pt")
    args = p.parse_args()
    if args.steps < 1 or args.batch_size < 1 or args.eval_interval < 1 or args.eval_batches < 1:
        p.error("steps, batch-size, eval-interval ed eval-batches devono essere positivi")
    if args.n_embd % args.n_head:
        p.error("n-embd deve essere divisibile per n-head")
    args.input, args.tokenizer, args.out = [x.expanduser().resolve() for x in (args.input, args.tokenizer, args.out)]
    try:
        import numpy as np
        import torch
        from clara_core.model import ModelConfig, ClaraGPT
    except ImportError as exc:
        raise SystemExit("Dipendenze mancanti: attiva .venv e usa `python -m pip install -r requirements.txt`.") from exc

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.train_tokenizer or not args.tokenizer.exists():
        print("Addestro il tokenizer BPE dai testi locali (nessun modello preaddestrato)...")
        source_iter = iter(iter_documents(args.input))
        first_document = next(source_iter, None)
        if first_document is None:
            raise SystemExit(f"Nessun testo leggibile in {args.input}. Esegui `python scripts/fetch_wikipedia.py --lang it --pages 200` o inserisci file .txt/.md/.jsonl autorizzati.")
        def tokenizer_stream():
            yield first_document[0]
            for text, _source in source_iter:
                yield text
        train_bpe_from_iterator(tokenizer_stream(), args.tokenizer, args.vocab_size)
    tokenizer = load_tokenizer(args.tokenizer)
    special = special_token_ids(tokenizer)
    tokens, corpus_hash, sources, docs, chars = make_tokens(args.input, tokenizer, special)
    # Keep tokens in compact host memory, not all on the GPU. The validation tail is held out.
    token_array = np.frombuffer(tokens, dtype=np.uint32)
    split = max(args.block_size + 2, int(len(token_array) * 0.98))
    split = min(split, len(token_array) - (args.block_size + 2))
    train_data, val_data = token_array[:split], token_array[split:]
    if len(train_data) < args.block_size + 2 or len(val_data) < args.block_size + 2:
        raise SystemExit(
            f"Corpus insufficiente per block-size={args.block_size}: {len(token_array)} token totali. "
            "Aggiungi dati o prova --block-size 128. Per un modello migliore serve molto più testo."
        )

    device_name = choose_device(torch, args.device)
    device = torch.device(device_name)
    torch.manual_seed(args.seed); np.random.seed(args.seed); random.seed(args.seed)
    if device_name == "cuda": torch.cuda.manual_seed_all(args.seed)

    start_step = 0
    if args.resume:
        payload = torch.load(args.resume.expanduser().resolve(), map_location="cpu", weights_only=False)
        if payload.get("tokenizer_kind") != "byte-level-bpe":
            raise SystemExit("Il checkpoint di ripresa non usa il tokenizer BPE di questa versione.")
        config = ModelConfig(**payload["config"])
        model = ClaraGPT(config)
        model.load_state_dict(payload["model_state_dict"])
        start_step = int(payload.get("step", 0))
    else:
        config = ModelConfig(vocab_size=tokenizer.get_vocab_size(with_added_tokens=True), block_size=args.block_size,
                             n_embd=args.n_embd, n_head=args.n_head, n_layer=args.n_layer, dropout=args.dropout)
        config.validate()
        model = ClaraGPT(config)
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.1, betas=(0.9, 0.95))
    if args.resume and payload.get("optimizer_state_dict"):
        try: optimizer.load_state_dict(payload["optimizer_state_dict"])
        except (ValueError, RuntimeError): print("[avviso] stato optimizer non compatibile: reinizializzato")

    params = sum(t.numel() for t in model.parameters())
    end_step = start_step + args.steps
    print(f"Avora Transformer | device={device_name} | parametri={params:,} | tokenizer BPE vocab={config.vocab_size:,}")
    print(f"Corpus={chars:,} caratteri / {len(token_array):,} token / {docs} documenti | train={len(train_data):,} val={len(val_data):,}")
    print(f"steps={start_step}->{end_step} | batch={args.batch_size} | block={config.block_size} | sha256={corpus_hash[:16]}")
    print("Training da inizializzazione casuale. La loss misura solo previsione del prossimo token, non qualità generale.")

    def get_lr(step: int) -> float:
        if args.warmup_steps > 0 and step < args.warmup_steps:
            return args.learning_rate * (step + 1) / args.warmup_steps
        progress = min(1.0, max(0.0, (step - args.warmup_steps) / max(1, args.steps - args.warmup_steps)))
        import math
        return args.min_learning_rate + 0.5 * (args.learning_rate - args.min_learning_rate) * (1 + math.cos(math.pi * progress))

    @torch.no_grad()
    def estimate_loss():
        model.eval(); result = {}
        for label, data in (("train", train_data), ("val", val_data)):
            losses = []
            for _ in range(args.eval_batches):
                x, y = sample_batch(np, torch, data, args.batch_size, config.block_size, device_name)
                _, loss = model(x, y); losses.append(float(loss.detach().cpu()))
            result[label] = sum(losses) / len(losses)
        model.train(); return result

    started = time.time()
    out_path = args.out
    def save_checkpoint(step: int, train_loss: float | None, val_loss: float | None):
        payload_out = {
            "format": "clara-gpt-v2", "tokenizer_kind": "byte-level-bpe",
            "tokenizer_path": str(args.tokenizer.relative_to(ROOT)) if args.tokenizer.is_relative_to(ROOT) else str(args.tokenizer),
            "special_token_ids": special, "config": config.to_dict(),
            "model_state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
            "optimizer_state_dict": optimizer.state_dict(), "step": step,
            "train_loss": train_loss, "val_loss": val_loss,
            "corpus_sha256": corpus_hash, "corpus_documents": docs, "corpus_characters": chars,
            "corpus_sources": sources, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "initialized_from_pretrained": False,
        }
        temp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        torch.save(payload_out, temp_path); temp_path.replace(out_path)
        (ROOT / "checkpoints" / "training-report.json").write_text(json.dumps({
            "stage": "pretraining", "step": step, "total_steps_requested": end_step,
            "train_loss": train_loss, "validation_loss": val_loss, "parameters": params,
            "vocab_size": config.vocab_size, "device": device_name, "corpus_sha256": corpus_hash,
            "documents": docs, "characters": chars, "token_count": len(token_array),
            "checkpoint": str(out_path), "initialized_from_pretrained": False,
            "warning": "Risultato sperimentale; non equivale a un assistente generalista.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    latest_losses = {"train": None, "val": None}
    try:
        for step in range(start_step + 1, end_step + 1):
            lr = get_lr(step - start_step - 1)
            for group in optimizer.param_groups: group["lr"] = lr
            x, y = sample_batch(np, torch, train_data, args.batch_size, config.block_size, device_name)
            _, loss = model(x, y)
            optimizer.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
            train_loss = float(loss.detach().cpu())
            if step == start_step + 1 or step % args.eval_interval == 0 or step == end_step:
                latest_losses = estimate_loss()
                elapsed = int(time.time() - started)
                print(f"step {step:>7}/{end_step} | train={latest_losses['train']:.4f} | val={latest_losses['val']:.4f} | lr={lr:.2e} | {elapsed}s")
                save_checkpoint(step, latest_losses["train"], latest_losses["val"])
            elif args.save_every > 0 and step % args.save_every == 0:
                save_checkpoint(step, train_loss, None)
    except KeyboardInterrupt:
        print("\nInterruzione richiesta: salvo un checkpoint prima di uscire.")
        save_checkpoint(step if "step" in locals() else start_step, train_loss if "train_loss" in locals() else None, latest_losses.get("val"))
        return
    save_checkpoint(end_step, latest_losses.get("train"), latest_losses.get("val"))
    print(f"\nCheckpoint salvato in: {out_path}")
    print("Per insegnare a seguire istruzioni, esegui poi scripts/finetune.py su esempi prompt/risposta autorizzati.")

if __name__ == "__main__": main()
