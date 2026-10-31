"""Tokenizer byte-level BPE trained from scratch on the user's corpus.

This uses the `tokenizers` implementation for BPE mechanics, not a pretrained
vocabulary or a pretrained language model. The vocabulary is learned locally.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

SPECIAL_TOKENS = [
    "<|pad|>", "<|unk|>", "<|bos|>", "<|eos|>",
    "<|system|>", "<|user|>", "<|assistant|>",
]


def require_tokenizers():
    try:
        from tokenizers import Tokenizer, decoders, models, normalizers, pre_tokenizers, trainers
    except ImportError as exc:
        raise SystemExit(
            "Manca il pacchetto tokenizers. Attiva .venv e installa le dipendenze con "
            "`python -m pip install -r requirements.txt`."
        ) from exc
    return Tokenizer, decoders, models, normalizers, pre_tokenizers, trainers


def train_bpe_from_iterator(text_iterator: Iterable[str], out_path: Path, vocab_size: int = 4096,
                            min_frequency: int = 2) -> dict[str, int]:
    Tokenizer, decoders, models, normalizers, pre_tokenizers, trainers = require_tokenizers()
    if vocab_size < 300:
        raise ValueError("vocab_size deve essere almeno 300 per includere l'alfabeto byte-level")
    tokenizer = Tokenizer(models.BPE(unk_token="<|unk|>"))
    tokenizer.normalizer = normalizers.NFC()
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=min_frequency,
        special_tokens=SPECIAL_TOKENS,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=True,
    )
    tokenizer.train_from_iterator(text_iterator, trainer=trainer)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(out_path))
    ids: dict[str, int] = {}
    for token in SPECIAL_TOKENS:
        token_id = tokenizer.token_to_id(token)
        if token_id is None:
            raise RuntimeError(f"Tokenizer non contiene il token speciale {token}")
        ids[token] = int(token_id)
    return ids


def load_tokenizer(path: Path):
    Tokenizer, *_ = require_tokenizers()
    if not path.is_file():
        raise FileNotFoundError(f"Tokenizer non trovato: {path}")
    return Tokenizer.from_file(str(path))


def special_token_ids(tokenizer) -> dict[str, int]:
    ids = {}
    for token in SPECIAL_TOKENS:
        value = tokenizer.token_to_id(token)
        if value is None:
            raise ValueError(f"Tokenizer incompatibile: manca {token}")
        ids[token] = int(value)
    return ids
