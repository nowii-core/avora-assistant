/* Detects "create an image" requests in the browser so the interface can show the right
   progress state. Mirrors clara_core/image_intent.py (the server remains authoritative);
   tests/test_quality.py runs both implementations on the same sentences. */
const AvoraImageIntent = (() => {
  'use strict';
  const L = '(?<![\\p{L}\\p{N}_])';
  const T = '(?![\\p{L}\\p{N}_])';
  const NOUNS = 'immagine|immagini|foto|fotografia|fotografie|disegno|disegni|illustrazione|illustrazioni|logo|loghi|marchio|poster|locandina|sfondo|sfondi|wallpaper|copertina|ritratto|icona|banner|infografica|schema|schemi|diagramma|diagrammi|flowchart|mappa concettuale|grafico matematico|picture|image|illustration|drawing|render|mockup';
  const VERBS = 'generami|genera|generare|generarmi|generate|generi|creami|crea|creare|crearmi|crei|create|fammi|fai|fare|farmi|make|draw|disegnami|disegna|disegnare|disegnarmi|dipingi|dipingimi|realizzami|realizza|realizzare|realizzarmi|progettami|progetta|produci|elaborami|elabora';
  const DRAW = 'disegnami|disegna|disegnare|disegnarmi|dipingi|dipingimi|draw';
  const DESIRE = 'voglio|vorrei|mi serve|mi servirebbe|mi servono|ho bisogno di|mi occorre|mi occorrono|desidero';
  const CORE = 'immagine|foto|fotografia|logo|marchio|illustrazione|poster|locandina|disegno|wallpaper|sfondo|ritratto|icona|banner|copertina';
  const W = '[\\p{L}\\p{N}_]*';
  const NOT_IMAGE = new RegExp(`${L}(?:codice|script|funzione|programma|python|javascript|typescript|html|css|api|classe|libreria|comando|bash|sql|react|backend|frontend|algoritmo|pagina web|riga di comando|ridimension${W}|comprim${W}|convert${W}|carica${W}|ottimizz${W}|docker|container|dockerfile|come si|come posso|come faccio|tutorial|quale programma|quale app)${T}`, 'u');
  const QUESTION = new RegExp(`^(?:come|perché|perche|spiegami|insegnami|che cosa|cosa significa|quale|quali|dove|quando)${T}`, 'u');
  const VERB_NOUN = new RegExp(`${L}(?:${VERBS})${T}[^.?!]{0,80}?${L}(?:${NOUNS})${T}`, 'u');
  const DRAW_ONLY = new RegExp(`${L}(?:${DRAW})${T}\\s+\\S+`, 'u');
  const DESIRE_NOUN = new RegExp(`${L}(?:${DESIRE})${T}\\s+(?:una?|un'|l'|lo|la|delle|dei)?\\s*(?:${CORE})${T}`, 'u');
  const BARE = new RegExp(`^(?:${CORE})\\s+(?:di|del|della|dei|delle|con|raffigurante|che raffigura)${T}`, 'u');

  function normalize(text) { return String(text || '').split(/\s+/).filter(Boolean).join(' ').trim().toLowerCase(); }

  function detect(message) {
    const value = normalize(message);
    if (!value || value.length > 12000) return false;
    if (QUESTION.test(value) || NOT_IMAGE.test(value)) return false;
    if (VERB_NOUN.test(value)) return true;
    if (DRAW_ONLY.test(value)) return true;
    if (DESIRE_NOUN.test(value)) return true;
    return value.length <= 220 && BARE.test(value);
  }

  return { detect };
})();
if (typeof window !== 'undefined') window.AvoraImageIntent = AvoraImageIntent;
