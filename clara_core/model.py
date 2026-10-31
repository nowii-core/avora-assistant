"""Avora Transformer (legacy Python class name ClaraGPT): decoder-only Transformer initialized from random weights.

No pretrained checkpoint is downloaded or loaded. Vocabulary size is determined
by the tokenizer trained specifically for this project's corpus.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import torch
from torch import nn
from torch.nn import functional as F

# Compatibility IDs for old v0.1/v0.2 byte-level checkpoints only.
EOS_ID = 256
BOS_ID = 257
VOCAB_SIZE = 258


@dataclass
class ModelConfig:
    vocab_size: int = VOCAB_SIZE
    block_size: int = 256
    n_embd: int = 128
    n_head: int = 4
    n_layer: int = 4
    dropout: float = 0.1

    def validate(self) -> None:
        if self.vocab_size < 8:
            raise ValueError("vocab_size deve essere almeno 8")
        if self.n_embd <= 0 or self.n_head <= 0 or self.n_layer <= 0:
            raise ValueError("Le dimensioni del modello devono essere positive")
        if self.n_embd % self.n_head:
            raise ValueError("n_embd deve essere divisibile per n_head")
        if self.block_size < 8:
            raise ValueError("block_size deve essere almeno 8")
        if not 0 <= self.dropout < 1:
            raise ValueError("dropout deve essere compreso tra 0 e 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CausalSelfAttention(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.n_head = config.n_head
        self.head_dim = config.n_embd // config.n_head
        self.qkv = nn.Linear(config.n_embd, 3 * config.n_embd, bias=False)
        self.proj = nn.Linear(config.n_embd, config.n_embd, bias=False)
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        mask = torch.tril(torch.ones(config.block_size, config.block_size, dtype=torch.bool))
        self.register_buffer("causal_mask", mask.view(1, 1, config.block_size, config.block_size), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, length, channels = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q = q.view(batch, length, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(batch, length, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(batch, length, self.n_head, self.head_dim).transpose(1, 2)
        scores = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        scores = scores.masked_fill(~self.causal_mask[:, :, :length, :length], float("-inf"))
        weights = self.attn_dropout(F.softmax(scores, dim=-1))
        out = weights @ v
        out = out.transpose(1, 2).contiguous().view(batch, length, channels)
        return self.resid_dropout(self.proj(out))


class FeedForward(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.n_embd, 4 * config.n_embd), nn.GELU(),
            nn.Linear(4 * config.n_embd, config.n_embd), nn.Dropout(config.dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TransformerBlock(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.n_embd)
        self.attention = CausalSelfAttention(config)
        self.ln2 = nn.LayerNorm(config.n_embd)
        self.feed_forward = FeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attention(self.ln1(x))
        x = x + self.feed_forward(self.ln2(x))
        return x


class ClaraGPT(nn.Module):
    """GPT-2-style language model. It begins with random weights."""
    def __init__(self, config: ModelConfig):
        super().__init__()
        config.validate()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.n_embd)
        self.position_embedding = nn.Embedding(config.block_size, config.n_embd)
        self.drop = nn.Dropout(config.dropout)
        self.blocks = nn.Sequential(*(TransformerBlock(config) for _ in range(config.n_layer)))
        self.final_norm = nn.LayerNorm(config.n_embd)
        self.language_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)
        self.apply(self._init_weights)
        self.language_head.weight = self.token_embedding.weight

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _, length = idx.shape
        if length > self.config.block_size:
            raise ValueError("La sequenza supera block_size")
        positions = torch.arange(length, device=idx.device)
        x = self.drop(self.token_embedding(idx) + self.position_embedding(positions)[None, :, :])
        x = self.final_norm(self.blocks(x))
        logits = self.language_head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1), ignore_index=-100)
        return logits, loss

    @torch.inference_mode()
    def generate(self, idx: torch.Tensor, max_new_tokens: int = 240, temperature: float = 0.85,
                 top_k: int = 40, eos_id: int = EOS_ID, bos_id: int = BOS_ID,
                 forbidden_ids: Iterable[int] | None = None) -> torch.Tensor:
        if temperature <= 0:
            raise ValueError("temperature deve essere maggiore di zero")
        self.eval()
        forbidden = [int(x) for x in (forbidden_ids or []) if 0 <= int(x) < self.config.vocab_size]
        if 0 <= bos_id < self.config.vocab_size and bos_id not in forbidden:
            forbidden.append(bos_id)
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.config.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            for token_id in forbidden:
                logits[:, token_id] = float("-inf")
            if top_k > 0:
                k = min(top_k, logits.size(-1) - len(forbidden) - 1)
                if k > 0:
                    values, _ = torch.topk(logits, k)
                    logits[logits < values[:, [-1]]] = float("-inf")
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)
            if int(next_token.item()) == eos_id:
                break
        return idx
