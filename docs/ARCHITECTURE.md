# Architettura di Avora v0.4.0

## Flusso applicativo predefinito

```text
Browser (UI bianca)
  └── HTTP locale 127.0.0.1:8765
        └── clara_core/server.py
              ├── clara_core/storage.py ── SQLite locale
              └── clara_core/runtime.py
                    └── endpoint Ollama locale 127.0.0.1:11434
                          └── modello open-weight scaricato dall'utente
```

Avora usa per impostazione predefinita un modello open-weight preaddestrato tramite Ollama per dare risposte utili senza implementare da zero l'intero training. Il modello iniziale è `qwen3:1.7b`. La UI e la cronologia sono di Avora; i pesi Qwen sono di terzi e non sono stati addestrati da nowii.

## Percorso sperimentale alternativo

Con `AVORA_ENGINE=transformer` il runtime può usare il Transformer incluso nel repository, cercando prima `checkpoints/avora-instruct.pt`, `checkpoints/avora.pt` e `checkpoints/avora-pretrain.pt`, poi i checkpoint legacy con nome `clara-*` e `nautilus-*`. La vecchia variabile `CLARA_ENGINE` resta supportata come fallback. Il Transformer è un decoder-only con causal self-attention, layer normalization, feed-forward GELU ed embedding token/posizione, inizializzato da pesi casuali. Usa una loss autoregressiva; SFT maschera la loss sul prompt.

La pipeline completa del laboratorio è in `docs/TRAINING.md`:

1. Acquisizione manuale facoltativa di testi con provenienza/licenza.
2. Audit del corpus con `scripts/check_corpus.py`.
3. Apprendimento del vocabolario byte-level BPE con `scripts/train_tokenizer.py`.
4. Pre-training con validazione, AdamW, clipping, scheduler e checkpoint riprendibili.
5. SFT su esempi JSONL di istruzioni.
6. Generazione CLI e valutazione manuale.

Questo percorso è educativo e indipendente da Ollama. Un corpus piccolo e poche migliaia di passi non producono un assistente equivalente ai modelli commerciali.

## Privacy e sicurezza

- Il server web ascolta su `127.0.0.1:8765`; non è un deploy pubblico.
- Il runtime predefinito invia messaggi solo al servizio locale `127.0.0.1:11434`, non a un'API cloud.
- Il primo download dei pesi richiede Internet; dopo il download la generazione avviene sul Mac.
- La cronologia SQLite, il corpus e i checkpoint restano nella cartella locale.
- Un modello può sbagliare o inventare informazioni; verifica le risposte importanti.


La versione 0.9.0 predefinisce Qwen3 1.7B per ridurre RAM e tempi sul Mac rispetto al tag 4B; la qualità può essere inferiore. Dalla versione 1.1.0 il contesto è di 8192 token e le risposte standard fino a circa 3000 token con continuazione automatica; i profili Equilibrato e Qualità sono selezionabili dall'app.
