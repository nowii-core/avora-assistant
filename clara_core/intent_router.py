"""Lightweight deterministic intent routing for Avora's general-purpose assistant.

The local LLM remains responsible for composing answers. This module selects when
fresh external evidence materially improves an answer and prepares a focused query.
It never fabricates search results or video URLs.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

WEB_INTENT_PATTERNS = (
    r"\bcerca(?:mi)? sul web\b", r"\bcerca(?:mi)? su internet\b", r"\bcerca(?:mi)? online\b",
    r"\bfai una ricerca(?: sul web| online| su internet)?\b", r"\bricerca approfondita\b",
    r"\bapprofondisci online\b", r"\b(?:cerca|trova) fonti\b", r"\bfonti aggiornate\b",
    r"\bfonti web\b", r"\bultime notizie\b", r"\bnotizie di oggi\b", r"\binformazioni aggiornate\b",
    r"\bdati aggiornati\b", r"\bprezz[oi] attual[ei]\b", r"\bquanto costa oggi\b", r"\bprezzo di oggi\b",
    r"\bultimi aggiornamenti\b", r"\bcita le fonti\b", r"\bconfronta le fonti\b",
    r"\bfonti ufficiali\b", r"\bverifica online\b", r"\bfai una ricerca completa\b",
)

# Requests whose correctness depends on the current date or changing public facts.
# Stable concepts/recipes/code remain local unless the user explicitly asks to search.
_CURRENT_FACT_TERMS = re.compile(
    r"\b(?:oggi|stasera|domani|ieri|adesso|attualmente|attuale|attuali|in questo momento|"
    r"in tempo reale|aggiornato|aggiornata|aggiornati|aggiornate|di recente|ultim[oi]|"
    r"ultim[ae] notizie|novità|quest['’]anno|anno corrente|ad oggi|nel 202[4-9]|"
    r"quanto costa|prezzo|prezzi|è uscito|e uscito|uscita|data di uscita|disponibile|"
    r"versione attuale|risultati|classifica|calendario|orario|a che ora|chi ha vinto|"
    r"chi è attualmente|chi e attualmente|meteo|previsioni del tempo|quando esce|quando esce il|"
    r"data di lancio|data di rilascio|è stato annunciato|e stato annunciato|ultima versione)\b", re.I
)

_HEALTH_TERMS = re.compile(
    r"\b(?:sintom[oi]|mi fa male|dolore|febbre|tosse|capogir[oi]|vertigini|nausea|vomito|"
    r"palpitazioni|respiro corto|fiato corto|pressione alta|pressione bassa|rash|eruzione cutanea|"
    r"allergia|allergico|infezione|medicinale|farmaco|effetti collaterali|dose|dosaggio|"
    r"mal di testa|mal di pancia|mal di stomaco|mal di gola|dolore al petto|dolore toracico|"
    r"ansia|attacco di panico|insonnia|problema di salute|problemi di salute|salute mentale|"
    r"è grave|e grave|devo preoccuparmi|devo andare dal medico|quando chiamare il medico)\b", re.I
)

_YOUTUBE_TERMS = re.compile(
    r"\b(?:youtube|you\s*tube|yt|link video|link ai video|mandami un video|mandami i video|"
    r"trovami un video|trovami i video|consigliami un video|consigliami dei video|video tutorial|tutorial video|"
    r"link per vedere|video che spiega|video su come|tutorial su youtube)\b", re.I
)
_SPORT_TERMS = re.compile(
    r"\b(?:calcio|serie\s*a|serie\s*b|champions(?:\s+league)?|europa league|conference league|"
    r"coppa italia|mondiali|europei|partite|partita|risultati|risultato|classifica|marcatori|"
    r"calendario|match|gioca|giocano|giocato|live score|punteggio)\b", re.I
)
_CURRENT_SPORT_TERMS = re.compile(
    r"\b(?:oggi|stasera|domani|ieri|adesso|ora|prossim[aeoi]|quando gioca|quando giocano|"
    r"risultati|classifica|calendario|partite|partita|live|in diretta|punteggio|a che ora|orario)\b", re.I
)
_PRODUCT_TERMS = re.compile(
    r"\b(?:telefono|telefoni|smartphone|iphone|samsung galaxy|pixel phone|cellulare|cellulari|"
    r"laptop|notebook|computer portatile|portatile|tablet|televisore|tv|cuffie|monitor|"
    r"scheda video|processore|console|fotocamera)\b", re.I
)
_CURRENT_QUERY_SHAPE = re.compile(
    r"\b(?:che|cosa|cos['’]è|chi|quando|quanto|quale|quali|dove|perché|perche|"
    r"dimmi|dammi|trovami|mostrami|fammi vedere|mi dici|mi trovi|mi mostri|"
    r"è il prezzo|e il prezzo|qual è|qual e|che cosa è successo)\b", re.I
)
_FACTUAL_QUESTION_TERMS = re.compile(
    r"\b(?:chi è|chi era|che cos['’]è|cos['’]è|cosa è|cosa sono|dove si trova|"
    r"quando è nato|quando è nata|quando è stato inventato|quando è stata inventata|"
    r"chi ha inventato|chi ha fondato|chi ha creato|a cosa serve|per cosa serve|"
    r"cosa fa la|cosa fa il|cosa fa|quali sono le differenze|qual è la differenza|"
    r"qual e la differenza|chi è il fondatore|chi è la fondatrice)\b", re.I
)
_PRODUCT_DECISION_TERMS = re.compile(
    r"\b(?:consigli[oa]?|consigliami|miglior[ei]?|quale|quali|confronta|differenze|comprare|"
    r"acquistare|conviene|prezzo|costa|budget|recensioni|top|classifica|vale la pena|"
    r"specifiche|caratteristiche|autonomia|fotocamera|prestazioni|confronto|consumi|opinioni)\b", re.I
)
_WEATHER_TERMS = re.compile(r"\b(?:meteo|previsioni del tempo|che tempo farà|che tempo fa|pioverà|piove oggi|temperatura oggi)\b", re.I)
_AI_MODEL_TERMS = re.compile(
    r"\b(?:intelligenza artificiale|ai|chatgpt|claude|gemini|deepseek|gpt[- ]?\d*|qwen|llama|mistral|copilot|perplexity|modelli linguistici)\b", re.I
)
_AI_COMPARE_TERMS = re.compile(
    r"\b(?:miglior[ei]|più potente|piu potente|confronta|confronto|differenze|ultim[oi]|novità|novita|"
    r"aggiornamenti|benchmark|classifica|quale conviene|quale scegliere|202[4-9])\b", re.I
)
_TRAVEL_TERMS = re.compile(r"\b(?:cosa vedere a|cosa fare a|posti da visitare|luoghi da visitare|ristoranti a|hotel a|eventi a|musei a)\b", re.I)
_RECIPE_TERMS = re.compile(
    r"\b(?:ricetta|ricette|ingredienti per|come cucinare|come si cucina|come si fa|come preparare|"
    r"prepara(?:mi)?|tempi di cottura|cottura perfetta)\b", re.I
)
_FOOD_TERMS = re.compile(
    r"\b(?:carbonara|amatriciana|pasta|pizza|risotto|lasagna|lasagne|tiramisù|tiramisu|"
    r"focaccia|pane|pollo|tacchino|manzo|pesce|salmone|gamberi|uova|torta|biscotti|"
    r"ragù|ragu|pesto|gnocchi|ravioli|pasta frolla|besciamella|frittata|polpette|verdure|"
    r"patate|curry|sushi|ramen|zuppa|vellutata|dolce|dessert|brioche|cornetto)\b", re.I
)
_CURRENCY_TERMS = re.compile(
    r"\b(?:cambio|tasso di cambio|valuta|valute|euro|dollari|sterline|franchi svizzeri|"
    r"yen|yuan|bitcoin|btc|ethereum|eth|exchange rate)\b", re.I
)


def classify_intent(message: str) -> str:
    """Choose a domain tool when the question needs fresh data or specialist safety."""
    value = " ".join(str(message or "").split()).strip().casefold()
    if not value:
        return "general"
    # Explanations about search itself are conceptual, not live search requests.
    if re.match(r"^(?:come funziona|spiegami come funziona|che cos['’]è|cosa significa)\b", value) and re.search(r"\b(?:ricerca web|cerca sul web|internet)\b", value):
        return "general"

    explicit_web = any(re.search(pattern, value, re.I) for pattern in WEB_INTENT_PATTERNS)
    if _YOUTUBE_TERMS.search(value):
        return "youtube"
    if _HEALTH_TERMS.search(value):
        # Vague health opener: invite a symptom description instead of broad web searching.
        if re.search(r"\b(?:ho un problema di salute|problemi di salute|posso chiederti una cosa sulla salute)\b", value) and not re.search(r"\b(?:sintom|dolore|febbre|tosse|nausea|vomito|mal di|pressione|respiro|fiato|medicinale|farmaco|allergia|grave)\b", value):
            return "health_general"
        return "health"
    if _SPORT_TERMS.search(value) and (_CURRENT_SPORT_TERMS.search(value) or explicit_web or re.search(r"\b(?:che partite|quali partite|partite di calcio|chi gioca|chi ha vinto|come è finita)\b", value)):
        return "sports"
    if _PRODUCT_TERMS.search(value) and (_PRODUCT_DECISION_TERMS.search(value) or _CURRENT_FACT_TERMS.search(value) or explicit_web):
        return "shopping"
    if _WEATHER_TERMS.search(value):
        return "weather"
    if _TRAVEL_TERMS.search(value):
        return "travel"
    if _RECIPE_TERMS.search(value) and _FOOD_TERMS.search(value):
        return "recipe"
    if _CURRENCY_TERMS.search(value) and re.search(r"\b(?:quanto|quanti|conversione|converti|vale|valore|cambio|oggi|attuale|attualmente|in euro|in dollari)\b", value):
        return "currency"
    if _AI_MODEL_TERMS.search(value) and (_AI_COMPARE_TERMS.search(value) or explicit_web or _CURRENT_FACT_TERMS.search(value)):
        return "ai_comparison"
    if _FACTUAL_QUESTION_TERMS.search(value):
        # "Chi è il presidente attuale?" depends on today's date; "Chi era Dante?" does not.
        return "web" if _CURRENT_FACT_TERMS.search(value) else "knowledge"
    if explicit_web:
        return "web"
    # Questions about current events, release dates, current facts, and price changes
    # are automatically searched even when the user doesn't say "search the web".
    if _CURRENT_FACT_TERMS.search(value) and _CURRENT_QUERY_SHAPE.search(value):
        return "web"
    if re.search(r"\b(?:ultime notizie|notizie di oggi|cosa è successo oggi|cosa e successo oggi|news di oggi|novità di oggi)\b", value):
        return "web"
    return "general"


def needs_web(intent: str) -> bool:
    # Stable knowledge (definitions, recipes, how-tos) is answered by the model directly: a web round trip
    # adds many seconds and, for a small model, more noise than value. Web is kept for data that changes.
    return intent in {"web", "sports", "youtube", "shopping", "health", "weather", "travel", "ai_comparison", "currency"}


def _italian_date(value: datetime) -> str:
    months = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")
    return f"{value.day} {months[value.month - 1]} {value.year}"


def build_search_query(message: str, intent: str, now: datetime | None = None) -> str:
    """Make the query more targeted without inventing any result or source."""
    original = " ".join(str(message or "").split()).strip()
    if intent == "youtube":
        subject = re.sub(r"\b(?:youtube|you\s*tube|yt|link|links|video|video\s*tutorial|tutorial|mandami|trovami|consigliami|mi trovi|mi mandi|dammi|per favore)\b", " ", original, flags=re.I)
        subject = re.sub(r"\s+", " ", subject).strip(" ,.:;- ") or original
        return f"site:youtube.com/watch {subject} tutorial video"[:500]
    if intent == "sports":
        current = now or datetime.now().astimezone()
        day = _italian_date(current)
        if re.search(r"\bdomani\b", original, re.I):
            day = _italian_date(current + timedelta(days=1))
        elif re.search(r"\bieri\b", original, re.I):
            day = _italian_date(current - timedelta(days=1))
        if re.search(r"\b(?:oggi|stasera|domani|ieri|adesso|ora)\b", original, re.I):
            return f"{original} {day} calcio calendario risultati orari fuso orario Italia"[:500]
        if re.search(r"\b(?:partite|partita|gioca|giocano|risultati|classifica|calendario|punteggio)\b", original, re.I):
            return f"{original} data e orario aggiornati calendario ufficiale risultati"[:500]
        return f"partite di calcio oggi {day} calendario risultati Serie A Champions League {original}"[:500]
    if intent == "shopping":
        return f"{original} specifiche tecniche recensioni affidabili prezzo Italia sito ufficiale confronto"[:500]
    if intent == "health":
        return f"{original} informazioni sanitarie affidabili linee guida site:iss.it OR site:salute.gov.it OR site:nhs.uk OR site:medlineplus.gov"[:500]
    if intent == "weather":
        return f"{original} previsioni meteo aggiornate data odierna"[:500]
    if intent == "travel":
        return f"{original} guida turistica ufficiale informazioni aggiornate"[:500]
    if intent == "ai_comparison":
        return f"{original} modelli AI aggiornati documentazione ufficiale benchmark indipendenti confronto 2026"[:500]
    if intent == "recipe":
        return f"{original} ricetta tradizionale ingredienti dosi procedimento sito cucina affidabile"[:500]
    if intent == "currency":
        return f"{original} cambio valuta aggiornato tasso di cambio corrente fonte finanziaria affidabile"[:500]
    if intent == "knowledge":
        return f"{original} spiegazione enciclopedica fonti affidabili documentazione ufficiale"[:500]
    return original[:500]


def intent_instructions(intent: str) -> str:
    """Behavior guidance appended to the system prompt for each routed request."""
    instructions = {
        "general": "Dai una risposta pratica, completa e verificabile, non una semplice panoramica.",
        "web": "Usa le fonti web fornite per rispondere; separa fatti, inferenze e incertezze. Non inventare citazioni.",
        "sports": (
            "Rispondi alla domanda sportiva usando solo le fonti web effettivamente fornite. Distingui partite in programma, "
            "risultati finali e partite in diretta; non inventare punteggi, orari o classifiche. Specifica la data e il fuso orario "
            "quando disponibile e metti in evidenza i link alle fonti ufficiali."
        ),
        "youtube": (
            "L'utente vuole video o link YouTube. Elenca i link diretti youtube.com effettivamente presenti nelle fonti fornite, "
            "con titolo e una breve descrizione. Non inventare ID o URL di video. Se i risultati non contengono video YouTube, "
            "dillo e fornisci solo eventuali risultati reali pertinenti."
        ),
        "shopping": (
            "Per consigli d'acquisto usa i risultati aggiornati forniti: confronta opzioni, specifiche, vantaggi, limiti e prezzi "
            "solo quando sono presenti nelle fonti. Non inventare disponibilità, valutazioni o prezzi. Se manca un budget, proponi "
            "fasce differenti senza bloccare la risposta. Distingui fatti verificati dai consigli personali."
        ),
        "health": (
            "Rispondi con informazioni sanitarie generali e cita le fonti mediche fornite. Non formulare una diagnosi certa, "
            "non sostituirti a medico o farmacista e non prescrivere o modificare dosaggi. Se mancano dettagli, chiedi sintomi, "
            "durata e gravità senza richiedere dati identificativi. Per dolore toracico, difficoltà respiratoria grave, perdita "
            "di coscienza, segni improvvisi di ictus, emorragia importante o altro pericolo immediato, indica di contattare subito "
            "i servizi di emergenza locali (in Italia 112/118). Non minimizzare segnali d'allarme."
        ),
        "health_general": (
            "Alla richiesta generica sulla salute rispondi con calma e senza diagnosticare: spiega che puoi offrire informazioni "
            "generali, poi chiedi qual è il disturbo, da quanto dura e quanto è intenso. Non chiedere nome, indirizzo o altri dati "
            "identificativi. Se c'è un pericolo immediato o difficoltà respiratoria grave, dolore toracico o segni di ictus, indica "
            "di chiamare i servizi di emergenza locali (in Italia 112/118)."
        ),
        "weather": "Fornisci previsioni solo se confermate da fonti aggiornate; indica località, data e incertezza.",
        "travel": "Proponi luoghi e attività basandoti sulle fonti fornite; non inventare orari, prezzi o disponibilità.",
        "ai_comparison": (
            "Confronta modelli e servizi AI usando fonti recuperate, separando caratteristiche dichiarate dai fornitori e benchmark indipendenti. "
            "Considera data, versione, disponibilità, privacy, costi e limiti. Non sostenere che un modello è migliore in assoluto senza criteri e prove."
        ),
        "recipe": (
            "Rispondi alla richiesta culinaria basandoti sulle ricette effettivamente recuperate. Dai porzioni, ingredienti con quantità, "
            "tempi e passaggi ordinati. Evidenzia differenze tra varianti tradizionali e adattamenti; non inventare che una variante sia l'unica autentica. "
            "Per sicurezza alimentare e temperature, privilegia fonti istituzionali o autorevoli."
        ),
        "currency": (
            "Per cambi di valuta o valori finanziari indica data e ora della fonte, valuta di partenza e di arrivo. "
            "Non trattare i valori come in tempo reale se le fonti non indicano un aggiornamento; non dare garanzie finanziarie."
        ),
        "knowledge": (
            "Rispondi a questa domanda fattuale basandoti sul contenuto effettivamente recuperato. Dai una risposta diretta prima dei dettagli, "
            "poi aggiungi il contesto più utile; se le fonti divergono, spiega la differenza. Cita link reali e non trasformare le ipotesi in fatti."
        ),
    }
    return instructions.get(intent, instructions["general"])
