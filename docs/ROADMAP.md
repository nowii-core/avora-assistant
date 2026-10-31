# Roadmap

## v0.4.0 — Local model runtime
- Ollama locale come runtime predefinito, Qwen3 1.7B come modello iniziale.
- Verifica del servizio e del modello installato, selezione persistente del nome modello.
- Messaggi espliciti per servizio spento o modello mancante.
- UI bianca, cronologia SQLite, ricerca, rinomina, esportazione e impostazioni.
- Laboratorio Transformer da zero mantenuto come modalità separata.

## Prossimi miglioramenti
- Streaming token-by-token dal modello locale.
- Elenco dei modelli già installati selezionabile dall'interfaccia.
- Controlli per contesto massimo e limite token.
- Importazione file locale con indicizzazione, senza invio a servizi esterni.
- Benchmark ripetibile della qualità di risposta e controlli di regressione.

La roadmap non promette parità con i modelli di frontiera. L'addestramento di un modello competitivo richiede risorse, dati, valutazioni e iterazione su una scala molto più grande di un singolo portatile.
