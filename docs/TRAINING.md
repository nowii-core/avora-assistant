# Training Avora from scratch

Avora includes a decoder-only Transformer with randomly initialized parameters, a tokenizer trained from the project corpus, autoregressive pre-training, supervised instruction fine-tuning (SFT), local generation, metrics, and checkpoints. It does **not** load a third-party language model. PyTorch and the `tokenizers` library are software tools; `tokenizers` trains a new BPE vocabulary from your texts and is not a pretrained AI model.

This is a small research implementation. Running these scripts does not produce an assistant at ChatGPT/Claude/Gemini/DeepSeek quality. Frontier systems use much larger corpora, models, compute budgets, extensive data curation, instruction and preference training, and broad evaluation. A lower loss alone is not proof of good answers.

## 0. Requirements

- Python version supported by current PyTorch and `tokenizers` wheels.
- A few GB free for the Python environment, tokenizer, dataset and checkpoints.
- CPU works for smoke tests; compatible Apple Silicon Macs may use PyTorch MPS. Check `torch.backends.mps.is_available()` before assuming GPU acceleration is enabled.
- No Ollama, hosted model, pretrained weights, or external AI API is used.

## 1. Create the environment (macOS)

From the root of the extracted repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -c "import torch, tokenizers; print('torch', torch.__version__, 'tokenizers', tokenizers.__version__); print('MPS', torch.backends.mps.is_available())"
```

## 2. Collect a starter corpus

### Option A — texts you own or are allowed to use

Put UTF-8 `.txt`, `.md`, or `.jsonl` files in `data/corpus/`. JSONL accepts `text`, `content`, `completion`, `output`, or `body`; it can also read message lists. Do not include credentials, secrets, private messages, or personal data without a lawful basis.

### Option B — small optional Wikimedia starter

The app itself never makes web requests. To explicitly download a small starter set of encyclopedia text, run:

```bash
python scripts/fetch_wikipedia.py --lang it --pages 200
```

You may choose `en`, `es`, `fr`, or another available Wikipedia language code. The script records article title, URL, retrieval date, and license notice in `data/corpus/wikipedia-it.jsonl`. This dataset is only a few hundred pages, not enough for a general-purpose LLM. Wikipedia text is generally licensed under CC BY-SA 4.0 and/or GFDL, with possible page-level exceptions. Attribution and ShareAlike requirements may apply; review each source's current license and your intended distribution before use. Sources: Wikimedia's official content-reuse guide and Wikipedia Foundation reuse guidance (linked in the repository README).

You can mix languages by collecting distinct corpora, for example `--lang it`, `--lang en`, `--lang es`. A multilingual model only learns languages and registers represented in adequate amounts in its training data. A handful of pages in a language will not confer fluency.

### Audit before training

```bash
python scripts/check_corpus.py
```

Check the report in `data/processed/corpus-report.json`, then manually review sample files and their licences. Deduplication in this basic tool identifies exact duplicate documents; it does not remove all near-duplicates or personally identifying information.

## 3. Train tokenizer from scratch

```bash
python scripts/train_tokenizer.py --vocab-size 4096
```

This learns a byte-level BPE vocabulary from your local corpus and writes `checkpoints/tokenizer.json`. It uses no pretrained vocabulary. The vocabulary size is a ceiling; small corpora may produce fewer tokens. Do not retrain the tokenizer after pre-training without retraining the model, because token IDs would change.

## 4. Pre-train from random weights

For a first test on a laptop, begin small:

```bash
python scripts/train.py --steps 300 --batch-size 2 --block-size 128 --n-embd 64 --n-head 4 --n-layer 2 --device auto
```

A stronger but still small experiment:

```bash
python scripts/train.py --steps 3000 --batch-size 4 --block-size 256 --n-embd 128 --n-head 4 --n-layer 4 --device auto
```

The script trains the tokenizer automatically if it is missing. Training reports train/validation loss, corpus hash, model size, token count, device and checkpoint path. Checkpoints are written periodically, so `Ctrl+C` saves a checkpoint. To continue training a checkpoint with the same tokenizer and configuration:

```bash
python scripts/train.py --resume checkpoints/avora-pretrain.pt --steps 1000 --device auto
```

`--steps` counts additional steps when `--resume` is supplied. Avoid using a new corpus or tokenizer with an old checkpoint unless you understand that a tokenizer vocabulary must match the model exactly.

## 5. Teach it to follow instructions (SFT)

Pre-training teaches next-token prediction; it does not automatically teach the assistant format. Add verified JSONL examples in `data/instructions/` with one of these forms:

```json
{"prompt":"Spiega le liste in Python.","completion":"Una lista è una sequenza ordinata e modificabile..."}
{"instruction":"Scrivi una funzione somma.","output":"def somma(a, b):\n    return a + b"}
{"messages":[{"role":"user","content":"Che cos'è HTTP?"},{"role":"assistant","content":"HTTP è un protocollo..."}]}
```

Then run:

```bash
python scripts/finetune.py --init checkpoints/avora-pretrain.pt --data data/instructions/examples.jsonl --steps 500 --batch-size 2 --device auto
```

For a real experiment, use a carefully reviewed, much larger instruction set and a separate evaluation set. `data/instructions/examples.jsonl` contains only a few original examples to test the pipeline; it is not sufficient for a useful assistant and will likely cause overfitting if trained repeatedly.

SFT produces `checkpoints/avora-instruct.pt`. Avora loads this checkpoint first when the local server starts. Restart `python run.py` after training.

## 6. Test manually and evaluate honestly

Interactive CLI:

```bash
python scripts/generate.py --checkpoint checkpoints/avora-instruct.pt
```

Generate a report from a held-out prompt set:

```bash
python scripts/evaluate.py --checkpoint checkpoints/avora-instruct.pt --prompts data/instructions/evaluation.example.jsonl
```

The evaluator writes prompt, optional reference answer and generated output to a JSONL report for manual review. It deliberately does not invent an automatic quality score. Keep evaluation prompts separate from training data, compare versions on the same prompts and involve human review. A drop in validation loss only means the model predicts that validation text better.

## 7. Model scaling and language coverage

Recommended order of work:

1. Acquire permitted and varied text; maintain provenance, licence, language and date metadata.
2. Filter malformed text, boilerplate, duplicates, low-quality documents, secrets and unnecessary personal data.
3. Train the tokenizer once, then pre-train from random weights and checkpoint frequently.
4. Add instruction examples, quality review and safety evaluation.
5. Measure latency, memory use, loss, language coverage and response quality; scale model and corpus only after those basics work.

A consumer laptop can validate the engineering loop and train a small experimental model. It cannot realistically reproduce the data and compute scale of leading commercial assistants by itself. For much larger runs, add more compute or train on a budget you can sustain; this repository intentionally does not silently upload data or spend money.
