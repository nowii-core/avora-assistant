#!/usr/bin/env python3
"""Supervised instruction fine-tuning (SFT) for an Avora Transformer checkpoint."""
from __future__ import annotations
import argparse, json, random, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clara_core.model import ModelConfig, ClaraGPT
from clara_core.tokenizer import load_tokenizer, special_token_ids

DEFAULT_SYSTEM = "Sei Avora, un assistente utile, chiaro e onesto. Se non sai qualcosa, dillo."


def load_pairs(path: Path):
    paths = [path] if path.is_file() else sorted(path.rglob("*.jsonl"))
    pairs = []
    for file in paths:
        if file.suffix.lower() != ".jsonl":
            continue
        with file.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip(): continue
                try: item = json.loads(line)
                except json.JSONDecodeError: continue
                if not isinstance(item, dict): continue
                prompt = item.get("prompt", item.get("instruction", item.get("question")))
                answer = item.get("completion", item.get("output", item.get("answer", item.get("response"))))
                system = item.get("system", DEFAULT_SYSTEM)
                if isinstance(prompt, str) and isinstance(answer, str) and prompt.strip() and answer.strip():
                    pairs.append((str(system), prompt.strip(), answer.strip(), f"{file}:{line_no}"))
                elif isinstance(item.get("messages"), list):
                    msgs = item["messages"]
                    for i, message in enumerate(msgs[:-1]):
                        next_message = msgs[i + 1]
                        if not isinstance(message, dict) or not isinstance(next_message, dict): continue
                        if message.get("role") == "user" and next_message.get("role") == "assistant":
                            question, response = message.get("content"), next_message.get("content")
                            if isinstance(question, str) and isinstance(response, str) and question.strip() and response.strip():
                                pairs.append((str(system), question.strip(), response.strip(), f"{file}:{line_no}"))
    return pairs


def make_example(system, prompt, answer, tokenizer, special, block_size):
    prefix_text = f"<|system|>\n{system}\n<|user|>\n{prompt}\n<|assistant|>\n"
    prefix = [special["<|bos|>"]] + tokenizer.encode(prefix_text, add_special_tokens=False).ids
    response = tokenizer.encode(answer, add_special_tokens=False).ids + [special["<|eos|>"]]
    ids = prefix + response
    response_start = len(prefix)
    if len(ids) > block_size + 1:
        # Preserve the full answer when possible and keep the newest portion of the prompt.
        prefix_budget = max(1, block_size + 1 - len(response))
        prefix = prefix[-prefix_budget:]
        ids = prefix + response
        response_start = len(prefix)
    x = ids[:-1]
    y = ids[1:]
    # During SFT the loss is applied only to answer tokens and the EOS terminator.
    mask_count = max(0, response_start - 1)
    y[:mask_count] = [-100] * min(mask_count, len(y))
    return x, y


def main():
    p = argparse.ArgumentParser(description="Insegna ad Avora a seguire istruzioni con esempi autorizzati")
    p.add_argument("--init", type=Path, default=ROOT / "checkpoints" / "avora-pretrain.pt")
    p.add_argument("--data", type=Path, default=ROOT / "data" / "instructions" / "examples.jsonl")
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--learning-rate", type=float, default=5e-5)
    p.add_argument("--eval-interval", type=int, default=100)
    p.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    p.add_argument("--out", type=Path, default=ROOT / "checkpoints" / "avora-instruct.pt")
    args = p.parse_args()
    if args.steps < 1 or args.batch_size < 1: p.error("steps e batch-size devono essere positivi")
    init_path = args.init.expanduser().resolve(); data_path = args.data.expanduser().resolve(); out_path = args.out.expanduser().resolve()
    if not init_path.is_file(): raise SystemExit(f"Checkpoint iniziale non trovato: {init_path}. Esegui prima scripts/train.py.")
    try:
        import numpy as np
        import torch
    except ImportError as exc:
        raise SystemExit("Dipendenze mancanti: usa `python -m pip install -r requirements.txt`.") from exc
    payload = torch.load(init_path, map_location="cpu", weights_only=False)
    if payload.get("tokenizer_kind") != "byte-level-bpe":
        raise SystemExit("Il checkpoint iniziale non è un checkpoint BPE Clara v0.3.")
    tok_path = Path(payload.get("tokenizer_path", "checkpoints/tokenizer.json"))
    if not tok_path.is_absolute(): tok_path = ROOT / tok_path
    tokenizer = load_tokenizer(tok_path); special = special_token_ids(tokenizer)
    pairs = load_pairs(data_path)
    if len(pairs) < 5:
        raise SystemExit(f"Trovati solo {len(pairs)} esempi. Aggiungi almeno 5 coppie domanda/risposta in JSONL.")
    random.seed(1337); random.shuffle(pairs)
    val_count = max(1, min(len(pairs) // 10, 1000))
    val_pairs, train_pairs = pairs[:val_count], pairs[val_count:]
    config = ModelConfig(**payload["config"])
    model = ClaraGPT(config); model.load_state_dict(payload["model_state_dict"])
    if args.device == "auto":
        device_name = "cuda" if torch.cuda.is_available() else ("mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
    else: device_name = args.device
    if device_name == "cuda" and not torch.cuda.is_available(): raise SystemExit("CUDA non disponibile")
    if device_name == "mps" and not (getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()): raise SystemExit("MPS non disponibile")
    model.to(device_name)
    train_examples = [make_example(*row[:3], tokenizer, special, config.block_size) for row in train_pairs]
    val_examples = [make_example(*row[:3], tokenizer, special, config.block_size) for row in val_pairs]
    pad_id = special["<|pad|>"]

    def get_batch(examples):
        chosen = random.choices(examples, k=args.batch_size)
        x = torch.full((args.batch_size, config.block_size), pad_id, dtype=torch.long)
        y = torch.full((args.batch_size, config.block_size), -100, dtype=torch.long)
        for row, (x_ids, y_ids) in enumerate(chosen):
            length = min(config.block_size, len(x_ids))
            if length:
                x[row, :length] = torch.tensor(x_ids[:length], dtype=torch.long)
                y[row, :length] = torch.tensor(y_ids[:length], dtype=torch.long)
        return x.to(device_name), y.to(device_name)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01, betas=(0.9, 0.95))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"SFT supervisato | esempi training={len(train_examples)} | validazione={len(val_examples)} | device={device_name}")
    print("La qualità finale dipende da esempi ben scritti, numerosi e verificati. Gli esempi inclusi sono solo dimostrativi.")
    started = time.time(); latest = {"train": None, "val": None}
    @torch.no_grad()
    def eval_loss():
        model.eval(); result = {}
        for label, examples in (("train", train_examples), ("val", val_examples)):
            vals = []
            for _ in range(min(8, max(1, len(examples)))):
                x, y = get_batch(examples); _, loss = model(x, y)
                if loss is not None and torch.isfinite(loss): vals.append(float(loss.cpu()))
            result[label] = sum(vals) / len(vals) if vals else None
        model.train(); return result

    for step in range(1, args.steps + 1):
        model.train(); x, y = get_batch(train_examples); _, loss = model(x, y)
        if loss is None or not torch.isfinite(loss): raise SystemExit("Loss non valida. Controlla i dati SFT.")
        optimizer.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
        if step == 1 or step % args.eval_interval == 0 or step == args.steps:
            latest = eval_loss(); elapsed = int(time.time() - started)
            print(f"step {step:>6}/{args.steps} | train={latest['train']:.4f} | val={latest['val']:.4f} | {elapsed}s")
            save = {**payload, "format": "clara-gpt-instruct-v2", "model_state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                    "optimizer_state_dict": optimizer.state_dict(), "step": step, "sft_examples": len(pairs),
                    "sft_train_examples": len(train_pairs), "sft_validation_examples": len(val_pairs),
                    "sft_train_loss": latest["train"], "sft_validation_loss": latest["val"],
                    "sft_data_sources": sorted(set(row[3].split(":")[0] for row in pairs)),
                    "stage": "supervised-finetuning", "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "warning": "La loss SFT non prova che il modello sia accurato o sicuro."}
            temp_path = out_path.with_suffix(out_path.suffix + ".tmp"); torch.save(save, temp_path); temp_path.replace(out_path)
    print(f"Checkpoint istruito salvato: {out_path}")
    print("Avora caricherà prima avora-instruct.pt quando riavvierai run.py. Il vecchio nome clara-instruct.pt resta supportato.")

if __name__ == "__main__": main()
