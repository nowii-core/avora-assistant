# Changelog Avora

## 1.4.0
- Presentazione di benvenuto al primo avvio (nome, aspetto, motore, configurazione dei modelli in un clic, idee per iniziare).
- Modalità demo (`--demo`) con risposte di esempio dichiarate, senza Ollama; il browser si apre da solo (`--no-browser` per evitarlo).
- Avvio con doppio clic per macOS e Windows (installazione di Python e Ollama con winget); rimossi i nomi predefiniti dal profilo.
- Barra inferiore essenziale (Allega, Voce, Pensa, Esplora) e menu integrato "Avora Auto" con scelta del modello e del livello di ragionamento (Bassa, Media, Alta). L'uso di codice e ricerca web è ora automatico quando serve.
- Barra laterale comprimibile con un clic o Ctrl/Cmd + B; la scelta viene ricordata.
- Azioni sui messaggi: modifica e copia sui tuoi messaggi; utile, da migliorare, rigenera, copia e ascolta sulle risposte. Il feedback è salvato localmente.
- Nuovo logo viola coordinato con pulsanti e stati attivi; pulsanti primari e filtri attivi in viola.
- Impostazioni, Progetti, Esplora e Immagini condividono intestazioni, spaziature, raggi e ombre; tema scuro rifinito.
- Libreria di prompt: comando "/" nel campo messaggio, prompt predefiniti e personali con segnaposto.
- Anteprima rapida di foto e file allegati; barra di avanzamento del contesto con avviso a conversazione lunga.

## 1.3.0
- Selezione automatica del modello: richieste semplici con il modello veloce, complesse con quello più potente, senza scelte manuali.
- Configurazione guidata con un clic: Avora consiglia e scarica i modelli adatti alla RAM del computer.
- Nuovo design: saluto animato, compositore con bordo dinamico, ingresso dei messaggi, pulsante di scorrimento, rispetto di prefers-reduced-motion.
- Nuovo logo a stella sfumata; selettore modello (Auto o modelli installati) e livelli di ragionamento Bassa, Media, Alta nella barra superiore.
- Figure geometriche (cubo, quadrato, triangolo, cerchio, piramide...) generate subito in SVG esatto, senza modello; schemi e disegni tecnici anche come blocchi svg con anteprima.
- Consenso esplicito prima della generazione immagini online; fallback locale se non disponibile.

## 1.2.0
- Modalità Agente: il modello può chiamare strumenti (codice Python in sandbox, ricerca web) in più passaggi; i passaggi sono mostrati in tempo reale e salvati nella chat, i grafici prodotti diventano immagini della conversazione.
- Sandbox Python: processo isolato con limiti di CPU, memoria, file e tempo, rete e processi esterni disabilitati.
- Personalità selezionabili (codice, scrittura, analisi dati, tutor, business) e ruolo personalizzato, iniettati nel prompt di sistema.
- Pannello Anteprima per blocchi HTML, SVG e Markdown, in iframe isolato con CSP dedicata; copia e download.
- Contatore del contesto in tempo reale e riassunto della chat in una nuova conversazione (`/api/conversations/<id>/compact`).
- Foto: se manca il modello visivo l'app propone l'installazione guidata invece di mostrare comandi da terminale; fino a 4 foto per messaggio.
- Nuovi test per sandbox, agente, personalità e riassunto.

## 1.1.0
- Risposte complete: limiti di generazione alzati, continuazione automatica delle risposte troncate con ricucitura del testo, cronologia più ampia e finestra di contesto estesa.
- Streaming delle risposte (`/api/chat/stream`) con pulsante Stop; avvio del modello in background e prompt stabile per sfruttare la cache.
- Conversazione vocale a frasi: la voce parte alla prima frase, con prefetch della successiva; motore vocale di sistema istantaneo e quarta voce italiana; riascolto automatico dopo la risposta.
- Immagini dalla chat: rilevamento affidabile delle richieste (Python e JavaScript con test di parità), prompt migliorato dal modello, catena con fallback finale a illustrazione SVG locale sanificata; opzione AI Horde con consenso esplicito.
- Interfaccia: nuovo marchio, tema chiaro/scuro/automatico, dimensione del testo, impostazioni riorganizzate (Profilo, Aspetto, Voce, Risposte, Modello, Utilizzo, Dati, Info), tabelle e citazioni nelle risposte, allegati incollati o trascinati (fino a 4 foto e file di testo).
- Modelli: profili Veloce, Equilibrato e Qualità con download guidato e barra di avanzamento (`/api/models/pull`).
- Qualità: rimozione delle emoji dalle risposte (server e client), instradamento web più mirato, notifica esplicita quando la ricerca web non è raggiungibile.
- Utilizzo: limiti rinominati Standard, Esteso e Massimo (300.000, 1.000.000 e 3.000.000 token per 3 ore); rimossi prezzi e pulsante di pagamento dimostrativi.
- Sicurezza: script di tema esterno compatibile con la CSP; SVG generati filtrati da whitelist.

## 1.0.2
- Fix bloccante: aggiunto l'elemento `#refreshImages` atteso dal JavaScript; gli handler registrati dopo il riferimento nullo ora vengono collegati regolarmente.
- Cache busting degli asset aggiornato a v1.0.2.
- Aggiunto test che rileva selettori DOM mancanti nel wiring degli eventi.

## 1.0.1 — 2026-10-28

- La libreria Immagini raccoglie immagini generate, upload diretti e allegati immagine delle conversazioni salvate.
- Sostituito il generatore gratuito non affidabile come percorso predefinito con il generatore immagini locale sperimentale di Ollama su macOS (`x/flux2-klein`), attivabile solo dopo conferma esplicita perché il download è di diversi GB.
- Le richieste di schemi, mappe concettuali e diagrammi vengono trasformate in SVG con etichette testuali nitide usando il modello locale.
- Convalidata la firma PNG/JPEG/WebP degli upload e i contenuti delle immagini salvate.
- Corretto un doppio salvataggio del messaggio utente durante la creazione di immagini in chat.
- Incrementata la versione dell'app e del cache busting degli asset.


## 1.0.0 — 2026-10-28

- Avvio più resiliente del componente vocale: controllo preventivo di PyPI e timeout/retry limitati se la connessione non è disponibile.

- Espansa la ricerca web: dopo il recupero dei risultati, Avora tenta di leggere il contenuto testuale delle prime pagine pubbliche, con limiti di dimensione e timeout.
- Passati al modello estratti e contenuti delle pagine con istruzioni esplicite di trattarli come dati non attendibili e ignorare eventuali prompt presenti nelle fonti.
- Esteso il routing automatico per informazioni correnti, date di uscita, prezzi, prodotti, notizie e domande sportive; evitati falsi positivi su frasi quotidiane come “oggi ho voglia di carbonara”.
- Migliorati i controlli URL per escludere host locali, indirizzi IP non pubblici letterali, porte atipiche e redirect non validi.
- Aggiunti test per lettura delle pagine, contenuto realmente recuperato e routing di richieste aggiornate.
- Dichiarati esplicitamente i limiti: ricerca web non significa accesso a tutti i siti, e il modello locale non diventa equivalente a un grande modello cloud.

## 0.9.0 — 2026-10-28

- Rebranding dell'interfaccia a **Avora** con logo SVG sobrio; mantenute le chiavi e il database legacy per non perdere i dati dell'utente.
- Riconoscimento automatico delle richieste esplicite di ricerca web, motori pubblici multipli e collegamenti fonte cliccabili. I risultati non vengono simulati se la rete fallisce.
- Calcolo aritmetico locale e deterministico per espressioni supportate, incluso lessico italiano per le operazioni; problemi più complessi passano al modello locale con istruzioni mirate.
- Ridotto il bisogno di attivare manualmente la modalità Esplora; generazione immagini naturale dalla chat resta disponibile con consenso una tantum per AI Horde o chiave Pollinations.
- Aggiornate verifiche automatiche per UI, nome, ricerca web, calcoli e instradamento delle richieste.
- Nessuna modifica al modello open-weight selezionato, alla cronologia SQLite, alla voce, ai piani locali o al laboratorio Transformer da zero.

## 0.8.3
- Added working Explore search panel and image-generation gallery.
- Removed fake/offline labels from the main UI and prevented failed model calls from being persisted as assistant messages.
- Added image generation through an explicitly configured Pollinations API provider, local key storage with restrictive file permissions, image history and downloads.
- Improved mobile modal layouts and voice failure feedback.


### 0.8.2
- Compattato il riquadro di elaborazione; la risposta completa non viene più duplicata nel riquadro di avanzamento.
- Resa più robusta l'associazione delle risposte alla conversazione di origine durante la navigazione.
- Passato al runtime il contesto realmente troncato dal server, invece dell'elenco non ridotto.
- Ridotta la finestra a 2048 token e l'output standard a 320 token; `think=false` esplicito per Qwen3 nella chat normale.
- Aggiunto un singolo nuovo tentativo senza contesto storico quando il modello ripete una risposta precedente a una domanda non correlata.
- Disabilitata la cache di HTML/asset per evitare che Safari continui a usare JavaScript vecchio.


### Voce e conversazione audio
- Modalità conversazione vocale con orb animato, microfono e stati per ascolto, elaborazione e risposta.
- Pulsante “Ascolta” sotto ogni risposta e lettura automatica facoltativa.
- Voci neurali italiane selezionabili via `edge-tts` e voce locale di fallback.
- Il testo pronunciato usa un servizio online quando è disponibile; la UI lo dichiara. Higgsfield non è collegato.

---

### Avora 0.7.0

- Aggiunti i piani locali Free, Pro e Max con budget diversi: 20k, 80k e 200k token.
- Il contatore locale si resetta ogni 3 ore.
- Risposte Ollama lette in streaming; l'interfaccia mostra fasi collegate al backend e testo man mano che arriva.
- Aggiunto endpoint locale di avanzamento per validazione, contesto, ricerca web, fonti, generazione e salvataggio.
- UI piano esplicita che i prezzi sono indicativi e che account cloud/fatturazione non sono configurati.
- Conservati cronologia SQLite, profilo locale, immagini, personalizzazione e laboratorio Transformer opzionale.

## Limiti

Free/Pro/Max sono modalità demo locali, non abbonamenti acquistabili. Per pagamenti reali occorrono account autenticati e verifica delle sottoscrizioni su un backend sicuro. Le quote di uso locale sono aggirabili da chi controlla il computer o modifica il codice e non vanno usate per fatturazione reale.


### 0.8.1
- Fix the voice-mode restart loop and make microphone interaction turn-based.
- Add optional natural Italian neural TTS with explicit online disclosure and macOS fallback.
- Default to Qwen3 1.7B, reduce context and standard generation budget for faster local responses.

- Branding del laboratorio aggiornato: nuovi checkpoint `avora-*` e variabile `AVORA_ENGINE`; restano compatibili i checkpoint e le variabili legacy.
