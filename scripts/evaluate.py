#!/usr/bin/env python3
"""Generate a review report from a held-out JSONL prompt set; no automatic quality score."""
from __future__ import annotations
import argparse, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clara_core.model import ModelConfig, ClaraGPT
from clara_core.tokenizer import load_tokenizer, special_token_ids


def select_device(torch, value: str) -> str:
    if value != "auto":
        if value == "cuda" and not torch.cuda.is_available(): raise SystemExit("CUDA non disponibile")
        if value == "mps" and not (getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()): raise SystemExit("MPS non disponibile")
        return value
    if torch.cuda.is_available(): return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available(): return "mps"
    return "cpu"


def main():
    p = argparse.ArgumentParser(description="Genera risposte su un set di valutazione separato e salva un report per revisione umana")
    p.add_argument("--checkpoint", type=Path, default=ROOT / "checkpoints" / "avora-instruct.pt")
    p.add_argument("--prompts", type=Path, default=ROOT / "data" / "instructions" / "evaluation.example.jsonl")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--max-new-tokens", type=int, default=160)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    args = p.parse_args()
    checkpoint_path = args.checkpoint.expanduser().resolve(); prompts_path = args.prompts.expanduser().resolve()
    if not checkpoint_path.is_file(): raise SystemExit(f"Checkpoint non trovato: {checkpoint_path}")
    if not prompts_path.is_file(): raise SystemExit(f"Set di valutazione non trovato: {prompts_path}")
    try: import torch
    except ImportError as exc: raise SystemExit("Installa PyTorch con `python -m pip install -r requirements.txt`.") from exc
    prompts = []
    with prompts_path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip(): continue
            try: row = json.loads(line)
            except json.JSONDecodeError: continue
            if not isinstance(row, dict): continue
            prompt = row.get("prompt", row.get("question", row.get("instruction")))
            if isinstance(prompt, str) and prompt.strip():
                prompts.append({"id": row.get("id", str(line_no)), "prompt": prompt.strip(),
                                "reference": row.get("reference", row.get("expected")), "source_line": line_no})
    if not prompts: raise SystemExit("Nessuna domanda valida nel file JSONL.")
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if payload.get("tokenizer_kind") != "byte-level-bpe": raise SystemExit("Il checkpoint non usa il tokenizer BPE v0.3.")
    config = ModelConfig(**payload["config"]); model = ClaraGPT(config)
    model.load_state_dict(payload["model_state_dict"])
    device = select_device(torch, args.device); model.to(device); model.eval()
    tokenizer_path = Path(payload.get("tokenizer_path", "checkpoints/tokenizer.json"))
    if not tokenizer_path.is_absolute(): tokenizer_path = ROOT / tokenizer_path
    tokenizer = load_tokenizer(tokenizer_path); special = special_token_ids(tokenizer)
    forbidden = [special[t] for t in ("<|pad|>", "<|unk|>", "<|bos|>", "<|system|>", "<|user|>", "<|assistant|>")]
    out = args.out.expanduser().resolve() if args.out else ROOT / "reports" / f"evaluation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Checkpoint: {checkpoint_path.name} | prompts: {len(prompts)} | device: {device}")
    print("Il report non assegna un punteggio automatico di verità: revisiona manualmente le risposte.")
    with out.open("w", encoding="utf-8") as f:
        for i, item in enumerate(prompts, 1):
            text = f"<|system|>\nSei Avora. Rispondi in italiano in modo chiaro e onesto. Se non sai, dichiara l'incertezza.\n<|user|>\n{item['prompt']}\n<|assistant|>\n"
            ids = [special["<|bos|>"]] + tokenizer.encode(text, add_special_tokens=False).ids
            if len(ids) > config.block_size: ids = [ids[0]] + ids[-(config.block_size - 1):]
            x = torch.tensor([ids], dtype=torch.long, device=device)
            with torch.inference_mode():
                y = model.generate(x, max_new_tokens=min(args.max_new_tokens, config.block_size),
                                   temperature=args.temperature, top_k=40,
                                   eos_id=special["<|eos|>"], bos_id=special["<|bos|>"], forbidden_ids=forbidden)
            generated = y[0, len(ids):].tolist()
            eos_id = special["<|eos|>"]
            if eos_id in generated: generated = generated[:generated.index(eos_id)]
            answer = tokenizer.decode(generated, skip_special_tokens=True).strip()
            row = {"id": item["id"], "prompt": item["prompt"], "reference": item["reference"],
                   "generated": answer, "checkpoint": str(checkpoint_path), "stage": payload.get("stage", "pretraining"),
                   "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(prompts)}] {item['prompt'][:76]}")
    print(f"Report salvato: {out}")
    print("Confronta versioni sullo stesso set, senza usarlo per allenare il modello.")

if __name__ == "__main__": main()
