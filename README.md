<div align="center">
  <img src="assets/avora.svg" width="64" alt="Avora">
  <h1>Avora</h1>
  <p><strong>Assistente AI privato che gira sul tuo computer.</strong></p>
  <p>Versione 1.4.0 &middot; nowii-core &middot; Ollama locale &middot; SQLite</p>
</div>

---

Avora è un assistente AI con interfaccia di chat completa: risposte in streaming, cronologia, allegati, ricerca web, creazione di immagini e conversazione vocale. Conversazioni e file restano sul computer: non serve un account né una API cloud. Le uniche connessioni esterne sono quelle che attivi tu (ricerca web, voce naturale, generazione di immagini online).

Il motore di linguaggio è un modello open-weight eseguito da [Ollama](https://ollama.com). I pesi sono di terzi, con la propria licenza; il codice di Avora (server, interfaccia, integrazioni) è MIT.

## Funzioni

- **Agente con strumenti:** attiva *Agente* e Avora decide da sola se eseguire codice Python in una sandbox locale (calcoli, analisi di dati incollati o allegati, grafici con matplotlib) o cercare sul web; i passaggi sono visibili in "Strumenti usati" e i grafici compaiono nella chat. Richiede un modello con supporto agli strumenti (Qwen3 o Llama 3.1 e successivi). La sandbox usa un processo separato con limiti di tempo, memoria e file, senza rete: è una protezione di buon senso per codice scritto dal modello sul tuo computer, non un confine di sicurezza contro codice ostile.
- **Personalità:** Generale, Consulente di codice, Scrittore creativo, Data analyst, Tutor e Consulente business, più un ruolo personalizzato, cambiabili al volo dal menu sotto il campo di scrittura.
- **Anteprima e artefatti:** i blocchi HTML, SVG e Markdown hanno il pulsante *Anteprima* con pannello dedicato (vista, codice, copia, download). L'anteprima è statica e isolata: gli script non vengono eseguiti.
- **Contatore del contesto:** la barra sotto il campo mostra quanto contesto occupa la chat e, quando è quasi piena, offre *Riassumi chat*, che crea una nuova conversazione con il riassunto.
- **Risposte in streaming:** il testo compare mentre viene scritto, con pulsante Stop. Le risposte lunghe vengono proseguite automaticamente fino alla fine invece di interrompersi a metà.
- **Conversazione vocale reattiva:** l'audio parte alla prima frase mentre il resto è ancora in scrittura, poi Avora ti riascolta. Voce naturale (4 voci italiane) oppure voce di sistema immediata e offline.
- **Foto e file:** allega fino a 4 foto (anche incollate o trascinate) e file di testo o codice. L'analisi delle foto richiede un modello visivo nativo (Qwen3-VL): se manca, Avora propone di installarlo con un clic. L'audio non viene elaborato direttamente dal modello: il microfono usa il riconoscimento vocale del browser.
- **Immagini dalla chat:** scrivi "crea una foto di..." o "disegnami...". La catena di generazione: schema vettoriale per diagrammi, modello locale di Ollama (se installato), generatore online gratuito con consenso esplicito, illustrazione vettoriale locale come ultima risorsa. Così una richiesta di immagine produce sempre un risultato.
- **Ricerca web integrata:** attivata automaticamente per notizie, prezzi, sport, meteo e altri dati aggiornati, con fonti cliccabili. Se la rete non risponde, Avora lo dichiara.
- **Formattazione completa:** titoli, elenchi, tabelle, citazioni e blocchi di codice con copia.
- **Tema chiaro, scuro o automatico** e tre dimensioni del testo.
- **Modelli con installazione guidata:** Veloce, Equilibrato e Qualità, con download e avanzamento dentro l'app, senza terminale.
- **Cronologia e dati:** SQLite locale, ricerca, rinomina, esportazione ed eliminazione; progetti con istruzioni riutilizzabili.
- **Limite token opzionale** su finestra di 3 ore (Standard, Esteso, Massimo), senza costi.

## Requisiti

- macOS, Windows o Linux con [Ollama](https://ollama.com/download) installato e avviato.
- Python 3.10 o successivo (solo per il server locale).
- Spazio su disco per il modello: circa 1,4 GB (Veloce), 2,6 GB (Equilibrato) o 5,2 GB (Qualità).

## Avvio

**macOS:** avvia `Avvia-Avora-Mac.command` (se macOS lo blocca: `bash Avvia-Avora-Mac.command` dal Terminale).
**Linux:** `bash start-linux.sh`. **Windows:** doppio clic su `Avvia-Avora-Windows.bat` (installa Python e Ollama con winget se mancano).

Al primo avvio il browser si apre da solo e una presentazione guidata permette di scegliere nome e aspetto e di scaricare i modelli adatti al computer con un solo clic. Si può rivedere da Impostazioni, Info.

### Modalità demo

Per presentare l'interfaccia senza installare alcun modello: `Avvia-Demo-Mac.command`, `Avvia-Demo-Windows.bat` oppure `python3 run.py --demo`. Le risposte sono esempi preimpostati, dichiarati come tali nella chat. Opzioni utili: `--port`, `--no-browser`.
Poi apri <http://127.0.0.1:8765>.

Avvio manuale del solo server: `python3 run.py` (opzioni `--host`, `--port`).

## Scegliere il modello

Impostazioni, sezione Modello:

| Profilo | Modello | RAM consigliata | Uso |
|---|---|---|---|
| Veloce | qwen3:1.7b | 8 GB | risposte immediate, voce |
| Equilibrato | qwen3:4b | 8 GB o più | uso quotidiano, codice |
| Qualità | qwen3:8b | 16 GB o più | ragionamento e scrittura migliori |

Un modello locale non raggiunge i grandi servizi cloud: per risposte più accurate scegli un profilo più grande. Qualsiasi tag della libreria Ollama può essere inserito nelle impostazioni avanzate.

## Voce

Premi **Voce**, parla e fai una breve pausa. Avora risponde a voce mentre scrive e si rimette in ascolto. Il riconoscimento del microfono dipende dal browser (consigliati Chrome, Edge o Safari) e può usare un servizio esterno. La voce naturale usa Microsoft Edge Neural TTS tramite `edge-tts` (`requirements-voice.txt`, installato dal launcher macOS): il testo da leggere viene inviato al servizio. La voce di sistema non invia nulla in rete.

## Immagini

Per foto realistiche installa il modello locale (sezione Immagini, diversi GB) oppure attiva la generazione online gratuita tramite AI Horde: la descrizione viene inviata in forma anonima a worker volontari e può richiedere attesa. Senza queste opzioni Avora crea illustrazioni vettoriali locali.

## Privacy

- Il database è `data/nautilus.sqlite3` (nome storico del file): contiene le tue conversazioni, non pubblicarlo.
- La chat comunica solo con Ollama su `127.0.0.1:11434`.
- Ricerca web, voce naturale e generazione online sono opzionali e dichiarate nell'interfaccia.
- Un modello locale può sbagliare: verifica le informazioni importanti, soprattutto in ambito medico, legale e finanziario.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Struttura

```text
assets/        interfaccia (HTML, CSS, JavaScript, logo)
clara_core/    server, runtime Ollama, intenti, immagini, SQLite
scripts/       laboratorio opzionale: Transformer da zero
docs/          architettura, dati e licenze, Ollama, training
tests/         test automatici
run.py         avvio del server
```

Il Transformer da zero (`AVORA_ENGINE=transformer`) è un percorso didattico separato: vedi [docs/TRAINING.md](docs/TRAINING.md). Il nome interno del pacchetto `clara_core` è conservato per compatibilità.

## Licenza

Codice sotto licenza MIT. Modelli, voci e servizi esterni seguono le rispettive licenze e condizioni d'uso.
