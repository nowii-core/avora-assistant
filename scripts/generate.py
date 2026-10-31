#!/usr/bin/env python3
"""Interactive local CLI to manually inspect a Avora checkpoint."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clara_core.model import ModelConfig, ClaraGPT, BOS_ID, EOS_ID
from clara_core.tokenizer import load_tokenizer, special_token_ids


def main():
    p = argparse.ArgumentParser(description="Prova manualmente un checkpoint Avora locale")
    p.add_argument("--checkpoint", type=Path, default=ROOT / "checkpoints" / "avora-instruct.pt")
    p.add_argument("--max-new-tokens", type=int, default=160)
    p.add_argument("--temperature", type=float, default=0.8)
    args = p.parse_args()
    try: import torch
    except ImportError as exc: raise SystemExit("Installa PyTorch con `python -m pip install -r requirements.txt`.") from exc
    ckpt_path = args.checkpoint.expanduser().resolve()
    if not ckpt_path.exists(): raise SystemExit(f"Checkpoint non trovato: {ckpt_path}")
    payload = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    config = ModelConfig(**payload["config"]); model = ClaraGPT(config)
    model.load_state_dict(payload["model_state_dict"]); model.eval()
    tok_path = Path(payload.get("tokenizer_path", "checkpoints/tokenizer.json"))
    if not tok_path.is_absolute(): tok_path = ROOT / tok_path
    tokenizer = load_tokenizer(tok_path); special = special_token_ids(tokenizer)
    forbidden = [special[x] for x in ("<|pad|>", "<|unk|>", "<|bos|>", "<|system|>", "<|user|>", "<|assistant|>")]
    print("Avora CLI locale. Il modello è sperimentale; scrivi /exit per uscire.")
    while True:
        try: prompt = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if prompt.lower() in {"/exit", "/quit"}: break
        if not prompt: continue
        formatted = f"<|system|>\nSei Avora. Rispondi in italiano in modo chiaro e onesto.\n<|user|>\n{prompt}\n<|assistant|>\n"
        ids = [special["<|bos|>"]] + tokenizer.encode(formatted, add_special_tokens=False).ids
        ids = [ids[0]] + ids[-(config.block_size - 1):] if len(ids) > config.block_size else ids
        x = torch.tensor([ids], dtype=torch.long)
        with torch.inference_mode():
            y = model.generate(x, max_new_tokens=args.max_new_tokens, temperature=args.temperature,
                               top_k=40, eos_id=special["<|eos|>"], bos_id=special["<|bos|>"], forbidden_ids=forbidden)
        generated = y[0, len(ids):].tolist()
        if special["<|eos|>"] in generated: generated = generated[:generated.index(special["<|eos|>"])]
        print("Avora:", tokenizer.decode(generated, skip_special_tokens=True).strip() or "[nessun testo generato]")

if __name__ == "__main__": main()
