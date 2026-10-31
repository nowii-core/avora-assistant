# Runtime locale tramite Ollama

Avora comunica con `http://127.0.0.1:11434` utilizzando le API HTTP locali di Ollama. Il runtime predefinito seleziona `qwen3:1.7b`, ma il tag può essere cambiato dall'interfaccia o tramite `NAUTILUS_OLLAMA_MODEL`.

## Primo avvio su macOS

1. Scaricare e installare l'app ufficiale: <https://ollama.com/download/mac>.
2. Aprire Ollama da Applicazioni.
3. Avviare `Avvia-Avora-Mac.command`: controlla il servizio, scarica il tag selezionato se necessario e lancia il server Avora.
4. Aprire `http://127.0.0.1:8765`.

Installazione manuale equivalente:

```bash
ollama pull qwen3:1.7b
python3 run.py
```

Il primo download richiede Internet. Successivamente, la generazione avviene sul dispositivo. Avora non chiama il cloud Ollama né invia i prompt a servizi AI remoti nella configurazione predefinita.

## Cambiare modello

Salvare il tag del modello nelle Impostazioni di Avora, quindi copiare il comando `ollama pull <tag>` generato dall'app. Un tag salvato ma non scaricato non può generare risposte fino al completamento del pull.

## Usare il Transformer originale

Il repository mantiene una pipeline didattica da zero. Per scegliere quel runtime, avviare il server con `AVORA_ENGINE=transformer python3 run.py`. Il modello da zero è indipendente da Ollama e va addestrato sui testi scelti; la qualità non è garantita.


Per avere voci neurali naturali, usare il launcher macOS `Avvia-Avora-Mac.command`: crea un ambiente `.venv` e installa `requirements-voice.txt`. Questo servizio TTS è online; se non è raggiungibile, Avora tenta la sintesi vocale locale di macOS.


## Impostazioni rapide di Avora v0.9.0

Per mantenere la chat reattiva, il modello testuale predefinito è `qwen3:1.7b`, il contesto è di 8192 token e le risposte possono arrivare a circa 3000 token, con continuazione automatica (fino a 4 riprese) se il modello si ferma per lunghezza. In conversazione vocale le risposte sono brevi (circa 420 token). La modalità `think` è disattivata esplicitamente su Qwen3 quando non viene attivata dall'utente. Per analizzare immagini il modello predefinito è `qwen3-vl:2b`; è facoltativo e va scaricato solo se serve (`ollama pull qwen3-vl:2b`).
