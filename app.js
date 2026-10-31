(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const ICONS = {
    plus: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.2 4.2"/></svg>',
    sliders: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.5 9a7 7 0 0 1 12-2L20 12M4 12l2.5 5a7 7 0 0 0 12-2"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>',
    chevron: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>',
    menu: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    settings: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z"/><path d="M19.4 13.5a7.8 7.8 0 0 0 0-3l1.4-1.1-1.7-3-1.7.7a8 8 0 0 0-2.5-1.4L14.6 4h-3.2l-.3 1.7A8 8 0 0 0 8.6 7.1l-1.7-.7-1.7 3 1.4 1.1a7.8 7.8 0 0 0 0 3l-1.4 1.1 1.7 3 1.7-.7a8 8 0 0 0 2.5 1.4l.3 1.7h3.2l.3-1.7a8 8 0 0 0 2.5-1.4l1.7.7 1.7-3Z"/></svg>',
    edit: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/></svg>',
    download: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12M7 10l5 5 5-5M4 20h16"/></svg>',
    arrowUp: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
    info: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
    code: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/></svg>',
    book: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 0 4 22Z"/><path d="M4 5.5v14A2.5 2.5 0 0 1 6.5 17H20M8 7h8M8 10h7"/></svg>',
    fileText: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/></svg>',
    checkSquare: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="m7.5 12 3 3 6-6"/></svg>',
    lock: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/></svg>',
    copy: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></svg>',
    trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 10v6M14 10v6"/></svg>',
    externalLink: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9"/><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/></svg>',
    clock: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    globe: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></svg>',
    image: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>',
    folder: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/></svg>',
    paperclip: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8.5 12.5 6.8-6.8a4 4 0 0 1 5.7 5.7l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2"/></svg>',
    brain: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4a4 4 0 0 0-7 2.7A4.5 4.5 0 0 0 4 15a4 4 0 0 0 5 5l3-2V4ZM12 4a4 4 0 0 1 7 2.7A4.5 4.5 0 0 1 20 15a4 4 0 0 1-5 5l-3-2M8 8h.01M7 14h.01M16 8h.01M17 14h.01M12 9v6"/></svg>',
    mic: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/></svg>',
    volume: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10v4h4l5 4V6l-5 4H4Z"/><path d="M17 9a5 5 0 0 1 0 6M19 5a10 10 0 0 1 0 14"/></svg>',
    stop: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>'
  };
  ICONS.chevronRight = ICONS.chevron;
  $$('[data-icon]').forEach(node => { const key = node.dataset.icon.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase()); if (ICONS[key]) node.innerHTML = ICONS[key]; });

  const state = { conversationId: null, viewEpoch: 0, conversations: [], status: null, sending: false, panelOpen: false, projectsOpen: false, toastTimer: null, settings: {}, selectedImages: [], think: false, deepResearch: false, projects: [], progressStartedAt: 0, voiceSessionActive: false, voiceListening: false, voiceSpeaking: false, voiceProcessing: false, voiceRecognition: null, voiceRecognitionStarting: false, imageProviderAvailable: false, imageGalleryItems: [], imageGalleryFilter: 'all', imageInstallPolling: false, pendingImageMessage: null, voiceAudioContext: null, voiceAudioSource: null, speechResolver: null, activeSpeechButton: null, speechGeneration: 0, selectedFiles: [], abort: null, lastSpeaker: null, speechFinish: null, pull: null, pullAfter: null, pullPolling: false, agent: false, personas: [], preview: null, pendingFrameHtml: '', setupQueue: [], setupDismissed: false, setupRunning: false };
  const el = {
    sidebar: $('#sidebar'), newChat: $('#newChat'), historyList: $('#historyList'), historySearch: $('#historySearch'), historySearchWrap: $('#historySearchWrap'),
    welcome: $('#welcomeScreen'), conversation: $('#conversationScreen'), messages: $('#messages'), form: $('#chatForm'), input: $('#messageInput'), send: $('#sendButton'), charCount: $('#charCount'),
    overlay: $('#overlay'), panel: $('#settingsPanel'), toast: $('#toast'),
    renameCurrent: $('#renameCurrent'), exportCurrent: $('#exportCurrent'), displayName: $('#displayName'), profileName: $('#profileName'), profileAvatar: $('#profileAvatar'), enterToSend: $('#enterToSend'), compactMode: $('#compactMode'),
  };

  // ═══════════════════════════════════════════════════════════════
// 🌐 CONFIGURAZIONE CLOUD (Cloudflare Worker → Groq)
// ═══════════════════════════════════════════════════════════════
const WORKER_URL = 'https://avora-proxy.nowii-core-879.workers.dev';
const WORKER_MODEL = 'llama-3.1-8b-instant';

const CLOUD_MODE = /github\.io$|netlify\.app$|vercel\.app$|pages\.dev$|gitlab\.io$|web\.app$|firebaseapp\.com$/.test(location.hostname)
                || location.protocol === 'file:';

const CLOUD_STORE_KEY = 'avora-cloud-store-v1';
function loadCloudStore() {
  try { return JSON.parse(localStorage.getItem(CLOUD_STORE_KEY) || '{"conversations":[],"messages":{}}'); }
  catch { return { conversations: [], messages: {} }; }
}
function saveCloudStore(store) {
  try { localStorage.setItem(CLOUD_STORE_KEY, JSON.stringify(store)); }
  catch (e) { console.warn('[Avora] localStorage pieno:', e); }
}

async function cloudApi(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const store = loadCloudStore();
  let body = {};
  try { body = options.body ? (typeof options.body === 'string' ? JSON.parse(options.body) : options.body) : {}; } catch {}

  if (path === '/api/status') {
    return { engine: 'cloud', model_name: WORKER_MODEL, model_loaded: true, ollama_running: true, auto_model: false, demo: false, available_models: [WORKER_MODEL], vision_model: '', vision_model_loaded: false };
  }
  if (path === '/api/conversations' && method === 'GET') {
    return { conversations: store.conversations };
  }
  const m = path.match(/^\/api\/conversations\/([^/]+)$/);
  if (m) {
    const id = m[1];
    const convo = store.conversations.find(c => c.id === id);
    if (method === 'GET') {
      if (!convo) throw new Error('Conversazione non trovata');
      return { conversation: convo, messages: store.messages[id] || [] };
    }
    if (method === 'PATCH') {
      if (convo && body.title) { convo.title = body.title; convo.updated_at = new Date().toISOString(); saveCloudStore(store); }
      return { conversation: convo };
    }
    if (method === 'DELETE') {
      store.conversations = store.conversations.filter(c => c.id !== id);
      delete store.messages[id];
      saveCloudStore(store);
      return { ok: true };
    }
  }
  const mTrunc = path.match(/^\/api\/conversations\/([^/]+)\/truncate$/);
  if (mTrunc && method === 'POST') {
    const id = mTrunc[1];
    if (store.messages[id]) store.messages[id] = store.messages[id].slice(0, Number(body.keep) || 0);
    saveCloudStore(store);
    return { ok: true };
  }
  const mFb = path.match(/^\/api\/messages\/([^/]+)\/feedback$/);
  if (mFb && method === 'POST') {
    for (const cid in store.messages) {
      const msg = store.messages[cid].find(x => x.id === mFb[1]);
      if (msg) { msg.feedback = body.value || null; break; }
    }
    saveCloudStore(store);
    return { ok: true };
  }
  if (path === '/api/usage') {
    return { usage: { plan: 'free', plan_name: 'Free', tokens_used: 0, remaining_tokens: 300000, percent_used: 0, seconds_until_reset: 3600 } };
  }
  if (path === '/api/personas') {
    return { personas: [{ id: 'general', label: 'Generale', description: 'Assistente versatile per ogni tipo di richiesta.' }] };
  }
  if (path === '/api/progress') {
    return { progress: { phase: 'generating', detail: 'Generazione della risposta in corso…' } };
  }
  if (path === '/api/models/pull') {
    if (method === 'GET') return { pull: { active: false, phase: 'done' } };
    throw new Error('Download modelli non disponibili nella versione cloud.');
  }
  if (path === '/api/images') {
    return { generator: { available: false, configured: false, local_model_installed: false, horde_enabled: true, reason: 'Non disponibile nella versione cloud.' }, gallery: [], images: [], uploads: [] };
  }
  if (path.startsWith('/api/images/')) throw new Error('Generazione immagini non disponibile nella versione cloud.');
  if (path.startsWith('/api/settings/')) return { ok: true, configured: false };
  if (path === '/api/search') throw new Error('Ricerca web non disponibile nella versione cloud.');
  if (path === '/api/tts') throw new Error('TTS non disponibile — uso la voce di sistema del browser.');
  throw new Error(`Endpoint ${path} non disponibile nella versione cloud.`);
}

   async function api(path, options = {}) {
    if (CLOUD_MODE) return cloudApi(path, options); // <-- QUESTA ERA LA RIGA MANCANTE
    const response = await fetch(path, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
    let data;
    try { data = await response.json(); } catch { data = {}; }
    if (!response.ok) { const error = new Error(data.error || `Errore HTTP ${response.status}`); error.code = data.code || ''; error.details = data; throw error; }
    return data;
  }
  function toast(message) {
    el.toast.textContent = message; el.toast.classList.remove('hidden');
    clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => el.toast.classList.add('hidden'), 2600);
  }
  function formatDay(dateValue) {
    const date = new Date(dateValue); if (Number.isNaN(date.getTime())) return 'Precedenti';
    const today = new Date(); today.setHours(0, 0, 0, 0); const other = new Date(date); other.setHours(0, 0, 0, 0);
    const diff = Math.floor((today - other) / 86400000);
    if (diff <= 0) return 'Oggi'; if (diff === 1) return 'Ieri'; if (diff <= 7) return 'Ultimi 7 giorni'; return 'Precedenti';
  }
  function timeLabel(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }); }
  function escapeHTML(value) { return String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char])); }
  const PREVIEWABLE = new Set(['html', 'svg', 'markdown', 'md']);
  const EMOJI_RE = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B50}\u{2B55}\u{FE0F}\u{200D}\u{20E3}]/u;
  const EMOJI_ALL = new RegExp(EMOJI_RE.source, 'gu');
  function stripEmojiClient(text) {
    const value = String(text || '');
    if (!EMOJI_RE.test(value)) return value;
    return value.replace(EMOJI_ALL, '').replace(/[ \t]+([.,;:!?])/g, '$1');
  }
  function inlineMarkdown(text) {
    return text
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*\w])\*(?!\s)([^*\n]+?)\*(?![*\w])/g, '$1<em>$2</em>')
      .replace(/~~(.+?)~~/g, '<del>$1</del>');
  }
  function markdownLite(text) {
    const codeBlocks = [], inlineCodes = [];
    const pushBlock = (lang, code) => { const i = codeBlocks.length; codeBlocks.push({ lang: lang || 'testo', code: code.replace(/\n$/, '') }); return `\n@@BLOCK${i}@@\n`; };
    let safe = escapeHTML(stripEmojiClient(text));
    safe = safe.replace(/```([a-zA-Z0-9_+.#-]*)[ \t]*\n([\s\S]*?)```/g, (_, lang, code) => pushBlock(lang, code));
    safe = safe.replace(/```([a-zA-Z0-9_+.#-]*)[ \t]*\n([\s\S]*)$/, (_, lang, code) => pushBlock(lang, code));
    safe = safe.replace(/`([^`\n]+)`/g, (_, code) => { const i = inlineCodes.length; inlineCodes.push(code); return `@@INLINE${i}@@`; });
    const lines = safe.split('\n'); let html = ''; let paragraph = []; let list = null; let quote = [];
    const flush = () => { if (paragraph.length) { html += `<p>${inlineMarkdown(paragraph.join('\n')).replace(/\n/g, '<br>')}</p>`; paragraph = []; } };
    const closeList = () => { if (list) { html += `</${list}>`; list = null; } };
    const closeQuote = () => { if (quote.length) { html += `<blockquote>${inlineMarkdown(quote.join('<br>'))}</blockquote>`; quote = []; } };
    const closeAll = () => { flush(); closeList(); closeQuote(); };
    const isRow = line => /^\s*\|.*\|\s*$/.test(line);
    const isSeparator = line => /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(line) && line.includes('-');
    const cells = line => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim());
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const marker = line.match(/^@@BLOCK(\d+)@@$/);
      if (marker) { closeAll(); const block = codeBlocks[Number(marker[1])]; const index = Number(marker[1]); const previewable = PREVIEWABLE.has(String(block.lang).toLowerCase()); html += `<div class="code-block"><div class="code-head"><span>${escapeHTML(block.lang)}</span><div class="code-actions">${previewable ? `<button type="button" data-preview-code="${index}">Anteprima</button>` : ''}<button type="button" data-copy-code="${index}">Copia codice</button></div></div><pre><code>${block.code}</code></pre></div>`; continue; }
      if (isRow(line) && i + 1 < lines.length && isSeparator(lines[i + 1])) {
        closeAll(); const head = cells(line); i += 2; const rows = [];
        while (i < lines.length && isRow(lines[i])) { rows.push(cells(lines[i])); i += 1; }
        i -= 1;
        html += `<div class="table-wrap"><table><thead><tr>${head.map(cell => `<th>${inlineMarkdown(cell)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${head.map((_, index) => `<td>${inlineMarkdown(row[index] || '')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
        continue;
      }
      const heading = line.match(/^(#{1,4})\s+(.+)$/);
      if (heading) { closeAll(); const level = Math.min(4, heading[1].length + 1); html += `<h${level}>${inlineMarkdown(heading[2])}</h${level}>`; continue; }
      if (/^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line)) { closeAll(); html += '<hr>'; continue; }
      const quoted = line.match(/^&gt;\s?(.*)$/);
      if (quoted) { flush(); closeList(); quote.push(quoted[1]); continue; }
      const bullet = line.match(/^\s*[-*+]\s+(.+)$/); const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (bullet || ordered) { flush(); closeQuote(); const tag = bullet ? 'ul' : 'ol'; if (list !== tag) { closeList(); html += `<${tag}>`; list = tag; } html += `<li>${inlineMarkdown((bullet || ordered)[1])}</li>`; continue; }
      closeList(); closeQuote();
      if (!line.trim()) flush(); else paragraph.push(line);
    }
    closeAll();
    return html.replace(/@@INLINE(\d+)@@/g, (_, index) => `<code>${inlineCodes[Number(index)] || ''}</code>`);
  }
  async function copyText(text) {
    try { await navigator.clipboard.writeText(text); }
    catch { const area = document.createElement('textarea'); area.value = text; document.body.append(area); area.select(); document.execCommand('copy'); area.remove(); }
  }
  function renderMessage(message, mode = null) {
    const isUser = message.role === 'user'; const wrapper = document.createElement('article'); wrapper.className = `message ${isUser ? 'user' : 'assistant'}`;
    const main = document.createElement('div'); main.className = 'message-main';
    const meta = document.createElement('div'); meta.className = 'message-meta'; const name = document.createElement('strong'); name.textContent = isUser ? (state.settings.displayName || 'Utente') : 'Avora'; meta.append(name);
    if (message.created_at) { const time = document.createElement('time'); time.textContent = timeLabel(message.created_at); meta.append(time); }
    const content = document.createElement('div'); content.className = 'message-content';
    if (isUser) content.textContent = String(message.content || '').replace(/\n*File allegato: ([^\n]+)\n```[\s\S]*?\n```/g, '\nAllegato: $1').trim(); else content.innerHTML = markdownLite(message.content);
    main.append(meta, content); if (isUser) wrapper.dataset.raw = String(message.content || '');
    if (Array.isArray(message.attachments) && message.attachments.length) {
      const visibleAttachments = message.attachments.filter(attachment => isUser || (attachment.generated && /^\/api\/generated\/[a-f0-9]{32}$/.test(attachment.url || '')));
      if (visibleAttachments.length) {
        const attachmentRow = document.createElement('div'); attachmentRow.className = `message-attachments${isUser ? '' : ' generated-result'}`;
        visibleAttachments.slice(0, 4).forEach(attachment => {
          const image = document.createElement('img'); image.src = attachment.localPreview || attachment.url || ''; image.alt = attachment.prompt || attachment.name || 'Immagine allegata'; image.loading = 'lazy'; attachmentRow.append(image);
          if (!isUser && attachment.generated && attachment.url) {
            const download = document.createElement('a'); download.href = attachment.url; download.download = attachment.name || 'avora-immagine.png'; download.className = 'generated-inline-download'; download.textContent = 'Salva immagine'; attachmentRow.append(download);
          }
        });
        main.append(attachmentRow);
      }
    }
    main.append(buildMessageTools(message, isUser));
    const trace = (Array.isArray(message.attachments) ? message.attachments : []).filter(item => item && item.tool);
    if (!isUser && trace.length) main.insertBefore(buildToolTrace(trace), content.nextSibling);
    wrapper.append(main);
    wrapper.addEventListener('click', event => {
      const copyButton = event.target.closest('[data-copy-code]'); const previewButton = event.target.closest('[data-preview-code]');
      const blocks = [...content.querySelectorAll('.code-block')];
      if (copyButton) { const code = blocks[Number(copyButton.dataset.copyCode)]?.querySelector('pre code'); if (code) copyText(code.textContent).then(() => toast('Codice copiato')); }
      else if (previewButton) { const block = blocks[Number(previewButton.dataset.previewCode)]; if (block) openPreview({ lang: block.querySelector('.code-head span').textContent, code: block.querySelector('pre code').textContent }); }
    });
    return wrapper;
  }
  ICONS.thumbUp = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 11v9H4v-9Z"/><path d="M7 11l4-7a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.3l-1.2 6.6a2 2 0 0 1-2 1.6H7"/></svg>';
  ICONS.thumbDown = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 13V4h3v9Z"/><path d="M17 13l-4 7a2 2 0 0 1-2-2v-4H5.500a2 2 0 0 1-2-2.300l1.200-6.600a2 2 0 0 1 2-1.600H17"/></svg>';
  function toolButton(icon, label, handler, extra = '') {
    const b = document.createElement('button'); b.type = 'button'; b.className = `message-tool icon-only ${extra}`.trim(); b.innerHTML = icon; b.title = label; b.setAttribute('aria-label', label); b.addEventListener('click', handler); return b;
  }
  function messageIndex(node) { return [...el.messages.querySelectorAll('.message:not(.streaming)')].indexOf(node.closest('.message')); }
  function dropMessagesFrom(node) { const all = [...el.messages.querySelectorAll('.message')]; const start = all.indexOf(node.closest('.message')); all.slice(start).forEach(n => n.remove()); }
  function buildMessageTools(message, isUser) {
    const tools = document.createElement('div'); tools.className = `message-tools${isUser ? ' user-tools' : ''}`;
    const plain = () => (isUser ? String(message.content || '') : stripEmojiClient(message.content));
    const hasImages = Array.isArray(message.attachments) && message.attachments.some(item => item && !item.tool && !item.generated);
    if (isUser) {
      tools.append(toolButton(ICONS.copy, 'Copia messaggio', async () => { await copyText(plain()); toast('Testo copiato'); }));
      if (!hasImages) tools.append(toolButton(ICONS.edit, 'Modifica messaggio', event => startEdit(event.currentTarget, message)));
      return tools;
    }
    const sendFeedback = async (button, value) => {
      if (!message.id) return; const next = message.feedback === value ? '' : value;
      try { await api(`/api/messages/${message.id}/feedback`, { method: 'POST', body: JSON.stringify({ value: next }) }); message.feedback = next; syncFeedback(); toast(next === 'up' ? 'Grazie per il riscontro.' : (next === 'down' ? 'Riscontro registrato: tenterò di fare meglio.' : 'Riscontro rimosso.')); } catch (error) { toast(error.message); }
    };
    const up = toolButton(ICONS.thumbUp, 'Risposta utile', e => sendFeedback(e.currentTarget, 'up'), 'feedback-up');
    const down = toolButton(ICONS.thumbDown, 'Risposta da migliorare', e => sendFeedback(e.currentTarget, 'down'), 'feedback-down');
    const syncFeedback = () => { up.classList.toggle('active', message.feedback === 'up'); down.classList.toggle('active', message.feedback === 'down'); up.setAttribute('aria-pressed', String(message.feedback === 'up')); down.setAttribute('aria-pressed', String(message.feedback === 'down')); }; syncFeedback();
    const regen = toolButton(ICONS.refresh, 'Rigenera la risposta', event => regenerate(event.currentTarget));
    const copy = toolButton(ICONS.copy, 'Copia risposta', async () => { await copyText(plain()); toast('Testo copiato'); });
    const listen = toolButton(ICONS.volume, 'Ascolta la risposta', () => { if (state.activeSpeechButton === listen && state.voiceSpeaking) stopSpeaking(); else speakText(plain(), { button: listen }); }, 'message-listen');
    tools.append(up, down, regen, copy, listen); return tools;
  }
  async function regenerate(button) {
    if (state.sending || !state.conversationId) return;
    const all = [...el.messages.querySelectorAll('.message:not(.streaming)')]; const i = all.indexOf(button.closest('.message')); const prev = all[i - 1];
    if (!prev || !prev.classList.contains('user')) { toast('Non trovo la domanda da ripetere.'); return; }
    if (prev.querySelector('.message-attachments')) { toast('Questa risposta usa una foto: invia di nuovo il messaggio con la foto per rigenerarla.'); return; }
    const text = prev.dataset.raw || ''; if (!text) return;
    try { await api(`/api/conversations/${state.conversationId}/truncate`, { method: 'POST', body: JSON.stringify({ keep: i - 1 }) }); } catch (error) { toast(error.message); return; }
    dropMessagesFrom(prev); await sendMessage(text);
  }
  function startEdit(button, message) {
    if (state.sending) return; const article = button.closest('.message'); const content = article.querySelector('.message-content'); if (article.classList.contains('editing')) return;
    const original = String(message.content || ''); article.classList.add('editing'); const index = messageIndex(article);
    const area = document.createElement('textarea'); area.className = 'edit-area'; area.value = original; area.rows = Math.min(10, Math.max(2, original.split('\n').length)); area.maxLength = 12000; area.setAttribute('aria-label', 'Modifica il messaggio');
    const row = document.createElement('div'); row.className = 'edit-actions';
    const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'button-secondary'; cancel.textContent = 'Annulla';
    const save = document.createElement('button'); save.type = 'button'; save.className = 'button-primary'; save.textContent = 'Salva e invia'; row.append(cancel, save);
    content.hidden = true; content.after(area, row); area.focus();
    const close = () => { area.remove(); row.remove(); content.hidden = false; article.classList.remove('editing'); };
    cancel.addEventListener('click', close);
    save.addEventListener('click', async () => {
      const text = area.value.trim(); if (!text) return; if (text === original.trim()) { close(); return; }
      try { await api(`/api/conversations/${state.conversationId}/truncate`, { method: 'POST', body: JSON.stringify({ keep: index }) }); } catch (error) { toast(error.message); return; }
      dropMessagesFrom(article); await sendMessage(text);
    });
    area.addEventListener('keydown', event => { if (event.key === 'Escape') { event.stopPropagation(); close(); } else if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) save.click(); });
  }
  ICONS.panel = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M9.500 4v16"/></svg>';
  ICONS.updown = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 9 4-4 4 4M8 15l4 4 4-4"/></svg>';
  ICONS.check = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.500 4.500 4.500L19 7.500"/></svg>';
  $$('[data-icon]').forEach(node => { const key = node.dataset.icon.replace(/-([a-z])/g, (_, l) => l.toUpperCase()); if (ICONS[key] && !node.innerHTML.trim()) node.innerHTML = ICONS[key]; });
  const REASONING = [['low', 'Bassa', 'Rapido ed efficiente'], ['medium', 'Media', 'Profondità bilanciata'], ['high', 'Alta', 'Analisi approfondita, più lenta']];
  function renderModelMenu() {
    const pop = $('#modelPop'); if (!pop) return; const status = state.status || {}; const list = (status.available_models || []).filter(n => !/vl|embed/i.test(n));
    const current = status.auto_model ? 'auto' : (status.model_name || ''); const level = state.settings.reasoning || 'medium';
    $('#modelMenuLabel').textContent = `Avora ${current === 'auto' ? 'Auto' : current}`;
    pop.replaceChildren();
    const section = text => { const h = document.createElement('div'); h.className = 'pop-title'; h.textContent = text; pop.append(h); };
    const item = (title, detail, active, onPick) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'pop-item'; b.setAttribute('role', 'menuitemradio'); b.setAttribute('aria-checked', String(active));
      const t = document.createElement('span'); t.className = 'pop-text'; const strong = document.createElement('strong'); strong.textContent = title; const small = document.createElement('small'); small.textContent = detail; t.append(strong, small);
      const c = document.createElement('span'); c.className = 'pop-check'; c.innerHTML = active ? ICONS.check : ''; b.append(t, c); b.addEventListener('click', onPick); pop.append(b); };
    section('Modello');
    item('Auto', 'Sceglie da solo il modello più adatto', current === 'auto', async () => { try { await api('/api/settings/auto', { method: 'POST', body: JSON.stringify({ auto: true }) }); await refreshStatus(); } catch (error) { toast(error.message); } });
    list.forEach(name => item(name, 'Installato sul tuo computer', current === name, async () => { try { await api('/api/settings/model', { method: 'POST', body: JSON.stringify({ model: name }) }); await refreshStatus(); } catch (error) { toast(error.message); } }));
    const sep = document.createElement('div'); sep.className = 'pop-sep'; pop.append(sep); section('Ragionamento');
    REASONING.forEach(([id, label, detail]) => item(label, detail, level === id, () => { state.settings.reasoning = id; persistPreferences(); renderModelMenu(); }));
  }
  function toggleModelMenu(force) {
    const pop = $('#modelPop'); const open = force !== undefined ? force : pop.classList.contains('hidden'); pop.classList.toggle('hidden', !open); $('#modelMenuButton').setAttribute('aria-expanded', String(open)); if (open) renderModelMenu();
  }
  function setSidebarCollapsed(collapsed, remember = true) {
    document.querySelector('.app-shell').classList.toggle('sidebar-collapsed', collapsed);
    if (remember) { state.settings.sidebarCollapsed = collapsed; persistPreferences(); }
  }
  const TOOL_LABELS = { run_python: 'Codice Python eseguito in sandbox', web_search: 'Ricerca web' };
  function toolStep(name, input, output) {
    const step = document.createElement('div'); step.className = 'tool-step';
    if (input) { const label = document.createElement('b'); label.textContent = name === 'web_search' ? 'Ricerca' : 'Input'; const pre = document.createElement('pre'); pre.textContent = input; step.append(label, pre); }
    if (output) { const label = document.createElement('b'); label.textContent = 'Risultato'; const pre = document.createElement('pre'); pre.textContent = output; step.append(label, pre); }
    return step;
  }
  function buildToolTrace(items) {
    const details = document.createElement('details'); details.className = 'tool-trace';
    const summary = document.createElement('summary'); summary.textContent = `Strumenti usati (${items.length})`; details.append(summary);
    items.forEach(item => { const title = document.createElement('b'); title.className = 'tool-step-title'; const step = toolStep(item.name, item.input, item.output); const head = document.createElement('b'); head.textContent = `${TOOL_LABELS[item.name] || item.name}${item.ok === false ? ' · errore' : ''}`; step.prepend(head); details.append(step); });
    return details;
  }
  function showToolEvent(container, event) {
    let holder = container.querySelector('.tool-cards'); if (!holder) { holder = document.createElement('div'); holder.className = 'tool-cards'; container.append(holder); }
    let card = holder.querySelector(`[data-tool-index="${event.index}"]`);
    if (!card) { card = document.createElement('details'); card.className = 'tool-card running'; card.dataset.toolIndex = String(event.index); card.open = true; holder.append(card); }
    card.replaceChildren(); const summary = document.createElement('summary'); summary.textContent = `${TOOL_LABELS[event.name] || event.name}${event.status === 'start' ? '…' : (event.ok === false ? ' · errore' : '')}`; card.append(summary);
    card.append(toolStep(event.name, event.input || '', event.status === 'done' ? event.output : ''));
    card.classList.toggle('running', event.status === 'start'); card.classList.toggle('failed', event.status === 'done' && event.ok === false);
    if (event.status === 'done') card.open = false;
  }
  function animateIn(node) { node.classList.add('enter'); node.addEventListener('animationend', () => node.classList.remove('enter'), { once: true }); return node; }
  function showConversation() {
    el.welcome.classList.add('hidden'); el.conversation.classList.remove('hidden');
    el.renameCurrent.disabled = !state.conversationId; el.exportCurrent.disabled = !state.conversationId;
  }
  function showWelcome() {
    state.viewEpoch += 1; { const hello = $('#welcomeHello'); if (hello) hello.textContent = greetingText(); }
    el.conversation.classList.add('hidden'); el.welcome.classList.remove('hidden'); state.conversationId = null; el.messages.replaceChildren();
    el.renameCurrent.disabled = true; el.exportCurrent.disabled = true; closeSidebar(); renderHistory(); el.input.focus(); updateContextMeter(); renderSetupCard();
  }
  function updateProfile() {
    const name = (state.settings.displayName || 'Utente').trim() || 'Utente'; state.settings.displayName = name; el.profileName.textContent = name;
    const initial = name.slice(0, 1).toLocaleUpperCase('it');
    el.profileAvatar.textContent = initial; $('#accountAvatarFallback').textContent = initial;
    const avatar = state.settings.avatarData || '';
    if (avatar) { $('#accountAvatarImage').src = avatar; $('#accountAvatarImage').classList.remove('hidden'); $('#accountAvatarFallback').classList.add('hidden'); el.profileAvatar.style.backgroundImage = `url("${avatar}")`; el.profileAvatar.classList.add('has-photo'); }
    else { $('#accountAvatarImage').removeAttribute('src'); $('#accountAvatarImage').classList.add('hidden'); $('#accountAvatarFallback').classList.remove('hidden'); el.profileAvatar.style.backgroundImage = ''; el.profileAvatar.classList.remove('has-photo'); }
  }
  function renderHistory() {
    const query = el.historySearch.value.trim().toLocaleLowerCase('it');
    const filtered = state.conversations.filter(item => !query || `${item.title || ''} ${item.preview || ''}`.toLocaleLowerCase('it').includes(query));
    el.historyList.replaceChildren();
    if (!filtered.length) { const empty = document.createElement('div'); empty.className = 'history-empty'; empty.textContent = query ? 'Nessuna conversazione trovata.' : 'Le conversazioni compariranno qui.'; el.historyList.append(empty); return; }
    let activeGroup = '';
    for (const conversation of filtered) {
      const group = formatDay(conversation.updated_at); if (group !== activeGroup) { const heading = document.createElement('div'); heading.className = 'history-group'; heading.textContent = group; el.historyList.append(heading); activeGroup = group; }
      const button = document.createElement('button'); button.type = 'button'; button.className = `history-item${conversation.id === state.conversationId ? ' selected' : ''}`; button.title = conversation.title || 'Nuova conversazione';
      const icon = document.createElement('span'); icon.className = 'history-item-icon'; icon.innerHTML = ICONS.clock;
      const title = document.createElement('span'); title.className = 'history-item-title'; title.textContent = conversation.title || 'Nuova conversazione';
      const rename = document.createElement('span'); rename.className = 'history-item-rename'; rename.title = 'Rinomina'; rename.innerHTML = ICONS.edit; rename.setAttribute('role', 'button'); rename.tabIndex = 0;
      const remove = document.createElement('span'); remove.className = 'history-item-delete'; remove.title = 'Elimina'; remove.innerHTML = ICONS.trash; remove.setAttribute('role', 'button'); remove.tabIndex = 0;
      const stop = event => { event.preventDefault(); event.stopPropagation(); };
      rename.addEventListener('click', async event => { stop(event); await renameConversation(conversation); });
      rename.addEventListener('keydown', async event => { if (event.key === 'Enter' || event.key === ' ') { stop(event); await renameConversation(conversation); } });
      remove.addEventListener('click', async event => { stop(event); await deleteConversation(conversation); });
      remove.addEventListener('keydown', async event => { if (event.key === 'Enter' || event.key === ' ') { stop(event); await deleteConversation(conversation); } });
      button.append(icon, title, rename, remove); button.addEventListener('click', () => loadConversation(conversation.id)); el.historyList.append(button);
    }
  }
  async function refreshHistory() {
    try { const data = await api('/api/conversations'); state.conversations = data.conversations || []; renderHistory(); }
    catch (error) { console.error(error); toast(`Cronologia non disponibile: ${error.message}`); }
  }
  async function loadConversation(id) {
    const requestedViewEpoch = ++state.viewEpoch;
    try { const data = await api(`/api/conversations/${id}`); if (requestedViewEpoch !== state.viewEpoch) return; state.conversationId = id; el.messages.replaceChildren(); for (const message of data.messages || []) el.messages.append(renderMessage(message)); showConversation(); renderHistory(); scrollToBottom(); closeSidebar(); updateContextMeter(); }
    catch (error) { toast(error.message); }
  }
  function scrollToBottom() { el.conversation.scrollTop = el.conversation.scrollHeight; }
  function modelInstalled(name) {
    const list = (state.status && state.status.available_models) || [];
    return list.includes(name) || (!name.includes(':') && list.includes(`${name}:latest`));
  }
  function renderAutoCard() {
    const status = state.status || {}; const toggle = $('#autoModel'); if (!toggle) return;
    toggle.checked = Boolean(status.auto_model); renderModelMenu();
    const models = status.auto_models || {};
    $('#autoDetail').textContent = status.auto_model
      ? (models.fast && models.strong && models.fast !== models.strong ? `Attivo: ${models.fast} per le richieste semplici, ${models.strong} per codice, analisi e ragionamento.` : `Attivo. Con un solo modello installato (${models.strong || models.fast || 'nessuno'}) Avora lo usa sempre: installa un profilo più potente per migliorare le risposte difficili.`)
      : 'Disattivato: Avora usa sempre il modello scelto qui sotto.';
  }
  function renderModelPresets() {
    const status = state.status || {}; const current = status.model_name; const busy = Boolean(state.pull && state.pull.active);
    $$('.preset-card[data-preset]').forEach(card => {
      const name = card.dataset.preset; const installed = modelInstalled(name); const active = current === name && !status.auto_model;
      const badge = $('[data-preset-badge]', card); const button = $('[data-preset-action]', card);
      badge.textContent = active ? 'In uso' : (installed ? (status.auto_model ? 'Installato · automatico' : 'Installato') : 'Da scaricare'); badge.dataset.state = active ? 'active' : (installed ? 'installed' : 'missing');
      button.textContent = active ? 'In uso' : (installed ? 'Usa' : 'Scarica e usa'); button.disabled = active || busy; card.classList.toggle('is-active', active);
    });
    const visionLoaded = Boolean(status.vision_model_loaded); const badge = $('#visionBadge'); const button = $('#installVision');
    if (badge) { badge.textContent = visionLoaded ? 'Installato' : 'Da installare'; badge.dataset.state = visionLoaded ? 'installed' : 'missing'; }
    if (button) { button.classList.toggle('hidden', visionLoaded); button.disabled = busy; }
  }
  function showPull() {
    const pull = state.pull || {}; const box = $('#pullProgress'); if (!box) return;
    const visible = Boolean(pull.active) || pull.phase === 'error';
    box.classList.toggle('hidden', !visible); if (!visible) return;
    const percent = Number.isFinite(pull.percent) ? Math.max(0, Math.min(100, pull.percent)) : 0;
    $('#pullTitle').textContent = pull.phase === 'error' ? 'Download non riuscito' : `Download di ${pull.model || 'modello'}`;
    $('#pullPercent').textContent = pull.phase === 'error' ? '' : `${percent}%`; $('#pullBar').style.width = `${percent}%`; $('#pullDetail').textContent = pull.detail || '';
  }
  async function pollPull() {
    if (state.pullPolling) return; state.pullPolling = true;
    try {
      for (;;) {
        const data = await api('/api/models/pull'); state.pull = data.pull || {}; showPull(); renderModelPresets();
        if (!state.pull.active) break; await new Promise(resolve => setTimeout(resolve, 1000));
      }
      const pull = state.pull || {}; const after = state.pullAfter; state.pullAfter = null;
      if (pull.phase === 'done') {
        if (after === 'text') await api('/api/settings/model', { method: 'POST', body: JSON.stringify({ model: pull.model }) });
        else if (after === 'vision') await api('/api/settings/vision-model', { method: 'POST', body: JSON.stringify({ model: pull.model }) });
        await refreshStatus(); toast(`${pull.model} installato${after ? ' e attivato' : ''}.`);
      } else if (pull.phase === 'error') toast(pull.detail || 'Download non riuscito.');
    } catch (error) { toast(error.message || 'Non riesco a leggere lo stato del download.'); }
    finally { state.pullPolling = false; showPull(); renderModelPresets(); }
  }
  async function startPull(model, after) {
    try { const data = await api('/api/models/pull', { method: 'POST', body: JSON.stringify({ model }) }); state.pull = data.pull; state.pullAfter = after; showPull(); renderModelPresets(); void pollPull(); }
    catch (error) { toast(error.message); }
  }
  async function usePreset(name) {
    if (modelInstalled(name)) {
      try { await api('/api/settings/model', { method: 'POST', body: JSON.stringify({ model: name }) }); await refreshStatus(); toast(`Modello in uso: ${name}`); } catch (error) { toast(error.message); }
      return;
    }
    if (!confirm(`Scaricare ${name}? Il download occupa spazio su disco e può richiedere diversi minuti.`)) return;
    await startPull(name, 'text');
  }
  async function refreshStatus() {
    const setText = (selector, value) => { const node = $(selector); if (node) node.textContent = value; };
    try {
      state.status = await api('/api/status');
      const status = state.status || {};
      const loaded = Boolean(status.model_loaded);
      const modelName = status.model_name || (status.engine === 'ollama' ? 'qwen3:1.7b' : 'Transformer locale');
      const running = Boolean(status.ollama_running);
      const dot = $('#summaryStatusDot');
      if (dot) dot.className = `summary-status${loaded ? ' ready' : ''}`;
      setText('#settingsModelStatus', loaded ? `${modelName} pronto` : (status.engine === 'ollama' ? (running ? 'Modello non caricato' : 'Ollama non raggiungibile') : 'Modello sperimentale non caricato'));
      setText('#settingsModelDescription', loaded
        ? 'Il modello selezionato è pronto. La generazione viene eseguita tramite il motore configurato.'
        : (status.engine === 'ollama' ? (running ? `Ollama è attivo ma ${modelName} non è disponibile. Usa il comando qui sotto per installarlo.` : 'Avvia Ollama sul Mac e verifica il modello selezionato.') : 'Non è disponibile un checkpoint addestrato per il Transformer sperimentale.'));
      setText('#engineDetail', status.engine === 'ollama' ? 'Ollama locale' : 'Transformer sperimentale');
      setText('#modelDetail', modelName);
      setText('#visionDetail', status.vision_model || 'qwen3-vl:2b');
      setText('#weightsDetail', status.engine === 'ollama' ? 'Pesi preaddestrati del modello selezionato' : 'Checkpoint locale');
      if (status.engine === 'ollama') {
        const visionName = status.vision_model || 'qwen3-vl:2b';
        if (document.activeElement !== $('#visionModel')) $('#visionModel').value = visionName;
        const visionPull = `ollama pull ${visionName}`;
        setText('#pullVisionCommand', visionPull);
        const copyVision = $('#copyPullVision'); if (copyVision) copyVision.dataset.copy = visionPull;
        if (document.activeElement !== $('#ollamaModel')) $('#ollamaModel').value = modelName;
        const pullCommand = `ollama pull ${modelName}`;
        setText('#pullModelCommand', pullCommand);
        const copyModel = $('#copyPullModel'); if (copyModel) copyModel.dataset.copy = pullCommand;
      }
      renderModelPresets(); renderSetupCard(); renderAutoCard();
      setText('#composerHint', loaded ? 'Risposte generate dal modello selezionato.' : 'Apri Impostazioni, sezione Modello, per verificare la configurazione.');
    } catch (error) {
      // Keep diagnostics inside Settings; never put a fake offline/status message in chat.
      const dot = $('#summaryStatusDot'); if (dot) dot.className = 'summary-status';
      setText('#settingsModelStatus', 'Stato non disponibile');
      setText('#settingsModelDescription', 'Non riesco a leggere lo stato del motore locale. Verifica che Avora sia in esecuzione.');
      setText('#composerHint', 'Controlla il motore nelle impostazioni se una richiesta non parte.');
      console.warn('Avora status:', error);
    }
  }
  function setBusy(busy) {
    state.sending = busy; el.send.disabled = false; el.form.classList.toggle('busy', busy); el.send.classList.toggle('is-stop', busy);
    el.send.innerHTML = busy ? ICONS.stop : ICONS.arrowUp;
    el.send.title = busy ? 'Interrompi la generazione' : 'Invia'; el.send.setAttribute('aria-label', busy ? 'Interrompi la generazione' : 'Invia messaggio');
  }
  function stopGeneration() { if (state.abort) { try { state.abort.abort(); } catch {} } }
  function detectMathRequest(text) {
    const value = String(text || '').trim().toLocaleLowerCase('it-IT');
    return /\b(?:quanto fa|calcola|calcolami|risolvi|risolvimi|equazione|disequazione|derivata|integrale|percentuale|teorema|geometria|algebra|matematica|semplifica|fattorizza|sistema di equazioni|problema di fisica|dimostra che)\b/.test(value)
      || /(?:\d\s*[+*/^=]\s*\d|\b\d+\s*[-−]\s*\d+|\b[xyz]\s*[=+*/-])/.test(value);
  }

  function detectImageRequest(text) {
    const value = String(text || '').trim();
    return Boolean(value && window.AvoraImageIntent && window.AvoraImageIntent.detect(value));
  }
  function detectWebRequest(text) {
    const value = String(text || '').trim().toLocaleLowerCase('it-IT');
    if (!value || detectImageRequest(text)) return false;
    if (/^(?:come funziona|spiegami come funziona|che cos'è|cosa significa)\b/.test(value) && /\b(?:ricerca web|cerca sul web|internet)\b/.test(value)) return false;
    const explicit = /\b(?:cerca(?:mi)? sul web|cerca(?:mi)? su internet|cerca(?:mi)? online|fai una ricerca(?: sul web| online| su internet)?|ricerca approfondita|approfondisci online|cerca fonti|trova fonti|fonti aggiornate|fonti web|ultime notizie|notizie di oggi|ultime informazioni|informazioni aggiornate|prezzo attuale|prezzi attuali|prezzo di oggi|quanto costa oggi|dati aggiornati|cita le fonti|confronta le fonti|fonti ufficiali|verifica online)\b/.test(value);
    const youtube = /\b(?:youtube|you\s*tube|link yt|link video|mandami (?:un |dei )?video|trovami (?:un |dei )?video|consigliami (?:un |dei )?video|video tutorial|tutorial video|video su come|link ai video)\b/.test(value);
    const sports = /\b(?:calcio|serie a|serie b|champions|europa league|coppa italia|partite di calcio|partite|partita|risultati|classifica|calendario|quando gioca|chi gioca|punteggio live)\b/.test(value) && /\b(?:oggi|stasera|domani|ieri|partite|partita|risultati|classifica|calendario|quando gioca|chi gioca|live|orario|che partite|quali partite|chi ha vinto)\b/.test(value);
    const products = /\b(?:telefono|telefoni|smartphone|iphone|samsung galaxy|cellulare|laptop|notebook|tablet|cuffie|monitor|console|macbook|pixel)\b/.test(value) && /\b(?:consigli|consigliami|migliore|migliori|quale|quali|comprare|acquistare|conviene|prezzo|confronta|recensioni|budget|specifiche|autonomia|fotocamera|caratteristiche|disponibile|oggi)\b/.test(value);
    const health = /\b(?:sintomi|mi fa male|dolore al petto|febbre|mal di testa|mal di pancia|tosse persistente|respiro corto|fiato corto|effetti collaterali|farmaco|medicinale|devo preoccuparmi)\b/.test(value);
    const weather = /\b(?:meteo|previsioni del tempo|che tempo farà|che tempo fa|pioverà|piove oggi|temperatura oggi)\b/.test(value);
    const travel = /\b(?:cosa vedere a|cosa fare a|posti da visitare|luoghi da visitare|ristoranti a|hotel a|eventi a|musei a)\b/.test(value);
    const factual = /\b(?:chi è|chi era|che cos['’]è|cos['’]è|cosa è|cosa sono|dove si trova|quando è nato|quando è nata|chi ha inventato|chi ha fondato|a cosa serve|per cosa serve|quali sono le differenze|qual è la differenza)\b/.test(value);
    const recipe = /\b(?:ricetta|ricette|ingredienti per|come cucinare|come si cucina|come si fa|come preparare|tempi di cottura)\b/.test(value) && /\b(?:carbonara|amatriciana|pasta|pizza|risotto|lasagna|lasagne|tiramisu|tiramisù|focaccia|pane|pollo|pesce|torta|biscotti|ragù|ragu|pesto|gnocchi|uova|frittata|polpette|sushi|ramen)\b/.test(value);
    const currency = /\b(?:dollari|sterline|franchi svizzeri|euro|bitcoin|ethereum|tasso di cambio|valuta)\b/.test(value) && /\b(?:quanto|quanti|converti|conversione|vale|valore|cambio|oggi|attuale|in euro|in dollari)\b/.test(value);
    const aiCompare = /\b(?:intelligenza artificiale|chatgpt|claude|gemini|deepseek|qwen|llama|copilot|perplexity|modelli linguistici|\bai\b)\b/.test(value) && /\b(?:migliore|migliori|confronto|confronta|differenze|più potente|piu potente|ultimi|ultime|novità|novita|oggi|attuale|benchmark)\b/.test(value);
    const current = /\b(?:oggi|stasera|domani|ieri|attualmente|attuale|in questo momento|in tempo reale|ultime notizie|ultima versione|quando esce|data di uscita|versione aggiornata|quanto costa|prezzo)\b/.test(value) && /\b(?:che|cosa|chi|quando|quanto|quale|quali|dove|dimmi|dammi|trovami|mostrami|mi dici|mi trovi)\b/.test(value);
    return explicit || youtube || sports || products || health || weather || travel || currency || aiCompare || current;
  }

async function readChatStream(body, signal, onDelta, onTool) {
  if (CLOUD_MODE) return readCloudChatStream(body, signal, onDelta, onTool);
  const response = await fetch('/api/chat/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal });
  if (!(response.headers.get('Content-Type') || '').includes('ndjson')) {
    let data = {}; try { data = await response.json(); } catch {}
    const error = new Error(data.error || `Errore HTTP ${response.status}`); error.code = data.code || ''; throw error;
  }
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''; let final = null;
  const handle = line => {
    if (!line.trim()) return; let event; try { event = JSON.parse(line); } catch { return; }
    if (event.type === 'delta') onDelta(String(event.text || ''));
    else if (event.type === 'tool') { if (onTool) onTool(event); }
    else if (event.type === 'done') final = event;
    else if (event.type === 'error') { const error = new Error(event.error || 'Richiesta non completata'); error.code = event.code || ''; throw error; }
  };
  for (;;) {
    const { value, done } = await reader.read(); if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let index; while ((index = buffer.indexOf('\n')) >= 0) { handle(buffer.slice(0, index)); buffer = buffer.slice(index + 1); }
  }
  buffer += decoder.decode(); handle(buffer);
  if (!final) throw new Error('Connessione interrotta prima della fine della risposta.');
  return final;
}

async function readCloudChatStream(body, signal, onDelta, onTool) {
  if (!WORKER_URL || WORKER_URL.includes('TUONOME')) {
    throw new Error('Configura WORKER_URL in app.js con l’URL del tuo Cloudflare Worker.');
  }
  if (Array.isArray(body.images) && body.images.length) {
    throw new Error('L’analisi delle foto non è disponibile nella versione cloud. Rimuovi la foto e riprova.');
  }

  const store = loadCloudStore();
  let convo = body.conversation_id ? store.conversations.find(c => c.id === body.conversation_id) : null;
  const isNew = !convo;
  if (!convo) {
    convo = {
      id: 'c_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title: 'Nuova conversazione',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }
  const existingMessages = store.messages[convo.id] || [];

  let systemPrompt = 'Sei Avora, un assistente AI utile, chiaro e cordiale. Rispondi sempre in italiano in modo naturale e conciso.';
  if (body.persona_prompt) systemPrompt += '\n\n' + body.persona_prompt;
  if (body.custom_instructions) systemPrompt += '\n\nIstruzioni personalizzate dall\'utente:\n' + body.custom_instructions;

  const history = [
    ...existingMessages.map(m => ({ role: m.role, content: m.content })),
    { role: 'user', content: body.message }
  ];
  const messages = [{ role: 'system', content: systemPrompt }, ...history];

  const response = await fetch(WORKER_URL, {
    method: 'POST',
    signal,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: WORKER_MODEL, messages, stream: true, temperature: 0.7 })
  });

  if (!response.ok) {
    let errText = '';
    try { errText = await response.text(); } catch {}
    throw new Error(`Worker errore ${response.status}: ${errText.slice(0, 200) || 'verifica il deploy e il secret GROQ_API_KEY'}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let fullText = '';
  let usage = null;

  const handleLine = (line) => {
    if (!line.startsWith('data:')) return;
    const payload = line.slice(5).trim();
    if (!payload || payload === '[DONE]') return;
    try {
      const event = JSON.parse(payload);
      const delta = event.choices && event.choices[0] && event.choices[0].delta && event.choices[0].delta.content;
      if (delta) { fullText += delta; onDelta(delta); }
      if (event.usage) usage = event.usage;
    } catch {}
  };

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf('\n')) >= 0) {
      handleLine(buffer.slice(0, idx).trim());
      buffer = buffer.slice(idx + 1);
    }
  }
  handleLine(buffer.trim());

  const userMsg = { id: 'm_' + Date.now() + '_u', role: 'user', content: body.message, created_at: new Date().toISOString() };
  const assistantMsg = { id: 'm_' + Date.now() + '_a', role: 'assistant', content: fullText, created_at: new Date().toISOString(), feedback: null };
  
  if (isNew) store.conversations.unshift(convo);
  store.messages[convo.id] = [...existingMessages, userMsg, assistantMsg];
  if (!convo.title || convo.title === 'Nuova conversazione') {
    convo.title = String(body.message).slice(0, 60).replace(/\s+/g, ' ').trim() || 'Nuova conversazione';
  }
  convo.updated_at = new Date().toISOString();
  saveCloudStore(store);

  return { conversation_id: convo.id, conversation: convo, assistant_message: assistantMsg, mode: 'cloud', metrics: usage ? { completion_tokens: usage.completion_tokens || 0 } : { completion_tokens: 0 } };
}
  

  // ---- Agent, personas, preview, context ----
  const AGENT_RE = /\b(grafic\w*|plot|disegna un grafico|esegui|eseguire|calcola|calcolo|simula\w*|csv|dataset|statistic\w*|media di|percentual\w*|ordina i numeri|script python|cerca sul web|ultime notizie)\b/i;
  function needsAgent(text) { return AGENT_RE.test(String(text || '')); }
  const FALLBACK_PERSONAS = [{ id: 'general', label: 'Generale', description: 'Assistente versatile per ogni tipo di richiesta.' }];
  async function loadPersonas() {
    try { state.personas = (await api('/api/personas')).personas || FALLBACK_PERSONAS; } catch { state.personas = FALLBACK_PERSONAS; }
    ['#personaSelect'].forEach(selector => { const select = $(selector); select.replaceChildren(); state.personas.forEach(item => select.append(new Option(item.label, item.id))); select.value = state.personas.some(item => item.id === state.settings.persona) ? state.settings.persona : 'general'; });
    syncPersona(state.settings.persona);
  }
  function syncPersona(id) {
    const valid = state.personas.some(item => item.id === id) ? id : 'general';
    state.settings.persona = valid; $('#personaSelect').value = valid;
    const item = state.personas.find(entry => entry.id === valid); $('#personaDescription').textContent = item ? item.description : '';
  }
  function changePersona(id) { syncPersona(id); persistPreferences(); const item = state.personas.find(entry => entry.id === state.settings.persona); if (item && item.id !== 'general') toast(`Personalità: ${item.label}`); }

  const PREVIEW_KINDS = { html: 'Documento HTML', svg: 'Immagine SVG', markdown: 'Documento Markdown', md: 'Documento Markdown' };
  const PREVIEW_MIME = { html: ['text/html', 'html'], svg: ['image/svg+xml', 'svg'], markdown: ['text/markdown', 'md'], md: ['text/markdown', 'md'] };
  function previewDocument(lang, code) {
    if (lang === 'html') return code;
    const style = 'body{font:15px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:760px;margin:24px auto;padding:0 22px;color:#202020;background:#fff}h1,h2,h3,h4{line-height:1.3}pre{background:#f4f4f4;padding:12px;border-radius:8px;overflow:auto}code{background:#f4f4f4;padding:1px 5px;border-radius:4px}table{border-collapse:collapse}th,td{border:1px solid #ddd;padding:6px 10px}blockquote{border-left:3px solid #ccc;margin:0;padding-left:14px;color:#555}';
    return `<!doctype html><meta charset="utf-8"><style>${style}</style>${markdownLite(code)}`;
  }
  function setPreviewTab(tab) {
    $$('[data-preview-tab]').forEach(button => button.classList.toggle('active', button.dataset.previewTab === tab));
    const item = state.preview; if (!item) return; const lang = item.lang.toLowerCase();
    const frame = $('#previewFrame'), image = $('#previewImage'), codeBox = $('#previewCode');
    frame.classList.add('hidden'); image.classList.add('hidden'); codeBox.classList.add('hidden');
    if (tab === 'code') { codeBox.textContent = item.code; codeBox.classList.remove('hidden'); return; }
    if (lang === 'svg') { image.replaceChildren(); const img = document.createElement('img'); img.alt = 'Anteprima SVG'; img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(item.code)}`; image.append(img); image.classList.remove('hidden'); return; }
    state.pendingFrameHtml = previewDocument(lang, item.code); frame.classList.remove('hidden'); frame.src = '/assets/artifact-frame.html';
  }
  function openPreview(item) {
    state.preview = { lang: String(item.lang || '').toLowerCase(), code: String(item.code || '') };
    $('#previewTitle').textContent = 'Anteprima'; $('#previewKind').textContent = PREVIEW_KINDS[state.preview.lang] || state.preview.lang;
    $('#previewPanel').classList.remove('hidden'); setPreviewTab('view');
  }
  function closePreview() { $('#previewPanel').classList.add('hidden'); $('#previewFrame').src = 'about:blank'; state.preview = null; }
  window.addEventListener('message', event => {
    const frame = $('#previewFrame'); if (!frame || event.source !== frame.contentWindow || !(event.data && event.data.ready)) return;
    frame.contentWindow.postMessage({ html: state.pendingFrameHtml }, '*');
  });

  // ---- Prompt library ----
  const DEFAULT_PROMPTS = [
    { title: 'Riassumi', body: 'Riassumi il testo seguente in 5 punti chiari, poi indica le azioni da intraprendere:\n\n{{testo}}' },
    { title: 'Correggi', body: 'Correggi grammatica e stile del testo seguente senza cambiarne il significato. Mostra solo la versione corretta:\n\n{{testo}}' },
    { title: 'Spiega semplice', body: 'Spiega in modo semplice, con un esempio concreto, il seguente argomento: {{testo}}' },
    { title: 'Revisione del codice', body: 'Fai una revisione del codice seguente: bug, sicurezza, prestazioni e leggibilità. Proponi la versione corretta completa.\n\n{{testo}}' },
    { title: 'Email professionale', body: 'Scrivi un\'email professionale, concisa e cordiale con questo obiettivo: {{testo}}' },
    { title: 'Traduci in inglese', body: 'Traduci in inglese naturale e professionale il testo seguente:\n\n{{testo}}' },
  ];
  function allPrompts() { return [...DEFAULT_PROMPTS, ...(Array.isArray(state.settings.prompts) ? state.settings.prompts : [])]; }
  function renderPromptList() {
    const box = $('#promptList'); if (!box) return; box.replaceChildren(); const custom = Array.isArray(state.settings.prompts) ? state.settings.prompts : [];
    if (!custom.length) { const p = document.createElement('p'); p.className = 'field-help'; p.textContent = 'Nessun prompt personale. Quelli predefiniti sono sempre disponibili.'; box.append(p); return; }
    custom.forEach((item, index) => { const row = document.createElement('div'); row.className = 'prompt-row'; const t = document.createElement('span'); t.textContent = item.title; const del = document.createElement('button'); del.type = 'button'; del.className = 'text-button'; del.textContent = 'Rimuovi'; del.addEventListener('click', () => { state.settings.prompts.splice(index, 1); persistPreferences(); renderPromptList(); }); row.append(t, del); box.append(row); });
  }
  let promptIndex = 0; let promptMatches = [];
  function updatePromptMenu() {
    const menu = $('#promptMenu'); const value = el.input.value;
    if (!value.startsWith('/') || value.includes('\n')) { menu.classList.add('hidden'); promptMatches = []; return; }
    const q = value.slice(1).toLowerCase(); promptMatches = allPrompts().filter(p => p.title.toLowerCase().includes(q)).slice(0, 8);
    if (!promptMatches.length) { menu.classList.add('hidden'); return; }
    promptIndex = Math.min(promptIndex, promptMatches.length - 1); menu.replaceChildren();
    promptMatches.forEach((p, i) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'prompt-option'; b.setAttribute('role', 'option'); b.setAttribute('aria-selected', String(i === promptIndex)); const s = document.createElement('strong'); s.textContent = p.title; const sm = document.createElement('small'); sm.textContent = p.body.replace(/\s+/g, ' ').slice(0, 90); b.append(s, sm); b.addEventListener('mousedown', e => { e.preventDefault(); applyPrompt(p); }); menu.append(b); });
    menu.classList.remove('hidden');
  }
  function applyPrompt(p) {
    $('#promptMenu').classList.add('hidden'); el.input.value = p.body; resizeInput(); updateCharCount(); el.input.focus();
    const at = p.body.indexOf('{{testo}}'); if (at >= 0) { el.input.value = p.body.replace('{{testo}}', ''); el.input.setSelectionRange(at, at); }
  }
  function onPromptKeys(event) {
    const menu = $('#promptMenu'); if (menu.classList.contains('hidden') || !promptMatches.length) return false;
    if (event.key === 'ArrowDown') { promptIndex = (promptIndex + 1) % promptMatches.length; updatePromptMenu(); event.preventDefault(); return true; }
    if (event.key === 'ArrowUp') { promptIndex = (promptIndex - 1 + promptMatches.length) % promptMatches.length; updatePromptMenu(); event.preventDefault(); return true; }
    if (event.key === 'Enter' || event.key === 'Tab') { applyPrompt(promptMatches[promptIndex]); event.preventDefault(); return true; }
    if (event.key === 'Escape') { menu.classList.add('hidden'); event.preventDefault(); return true; }
    return false;
  }
  // ---- File preview ----
  function openFilePreview(item, isImage) {
    $('#filePreviewTitle').textContent = item.name || 'File'; const img = $('#filePreviewImage'); const pre = $('#filePreviewText');
    img.classList.toggle('hidden', !isImage); pre.classList.toggle('hidden', isImage);
    if (isImage) { img.src = item.preview; img.alt = item.name || ''; $('#filePreviewMeta').textContent = item.mime || 'Immagine'; }
    else { const text = String(item.text || ''); pre.textContent = text.length > 20000 ? `${text.slice(0, 20000)}\n\n[... anteprima troncata ...]` : text; $('#filePreviewMeta').textContent = `${text.length.toLocaleString('it-IT')} caratteri · circa ${Math.round(text.length / 3).toLocaleString('it-IT')} token`; }
    $('#filePreviewLayer').classList.remove('hidden'); document.body.style.overflow = 'hidden';
  }
  function closeFilePreview() { $('#filePreviewLayer').classList.add('hidden'); if (!state.panelOpen && !state.projectsOpen) document.body.style.overflow = ''; }
  const HISTORY_CHARS = 14000;
  function updateContextMeter(lastTokens) {
    const meter = $('#contextMeter'); if (!meter) return;
    const nodes = [...el.messages.querySelectorAll('.message')].filter(node => !node.classList.contains('processing-message') && !node.classList.contains('streaming'));
    if (!state.conversationId || !nodes.length) { meter.classList.add('hidden'); return; }
    const chars = nodes.reduce((sum, node) => sum + ((node.querySelector('.message-content') || {}).textContent || '').length, 0);
    const percent = Math.min(100, Math.round(chars * 100 / HISTORY_CHARS)); const tokens = Math.round(Math.min(chars, HISTORY_CHARS) / 3);
    let text = `Contesto ${percent}% · circa ${tokens.toLocaleString('it-IT')} token`;
    if (lastTokens) text += ` · ultima risposta ${Number(lastTokens).toLocaleString('it-IT')}`;
    if (chars > HISTORY_CHARS) text += ' · i messaggi più vecchi non vengono più letti';
    $('#contextText').textContent = text; meter.classList.remove('hidden'); meter.classList.toggle('is-high', percent >= 90);
    $('#compactChat').classList.toggle('hidden', percent < 60); meter.style.setProperty('--pct', percent + '%');
    if (percent >= 85 && state.contextWarned !== state.conversationId) { state.contextWarned = state.conversationId; toast('La conversazione è lunga: usa "Riassumi chat" per mantenere il contesto e le risposte accurate.'); }
  }
  async function compactCurrentChat() {
    if (!state.conversationId || state.sending) return;
    if (!confirm('Riassumere questa chat? Verrà creata una nuova conversazione con un riassunto del contesto; la chat attuale resta salvata.')) return;
    const button = $('#compactChat'); button.disabled = true; button.textContent = 'Riassumo…';
    try { const data = await api(`/api/conversations/${state.conversationId}/compact`, { method: 'POST', body: JSON.stringify({}) }); await refreshHistory(); await loadConversation(data.conversation.id); toast('Nuova chat creata con il riassunto del contesto.'); }
    catch (error) { toast(error.message || 'Riassunto non riuscito.'); }
    finally { button.disabled = false; button.textContent = 'Riassumi chat'; }
  }

  // Photorealistic images without installing anything: offered once, with explicit consent.
  async function ensureImageConsent() {
    if (state.settings.hordeAsked) return;
    try {
      const data = await api('/api/images'); const generator = data.generator || {};
      if (generator.horde_enabled || generator.local_model_installed || generator.configured) { state.settings.hordeAsked = true; persistPreferences(); return; }
      state.settings.hordeAsked = true; persistPreferences();
      if (confirm('Per creare immagini realistiche senza installare nulla, Avora può usare la rete gratuita AI Horde. La descrizione dell’immagine viene inviata in forma anonima e la creazione può richiedere da pochi secondi a un minuto.\n\nAttivare? Se annulli, Avora creerà solo illustrazioni vettoriali locali. Puoi cambiare scelta in Immagini.')) {
        await api('/api/settings/image-consent', { method: 'POST', body: JSON.stringify({ consent: true }) });
        toast('Immagini realistiche attivate.');
      }
    } catch { /* the chat request reports any real problem */ }
  }
  function greetingText() {
    const hour = new Date().getHours(); const name = (state.settings.displayName && state.settings.displayName !== 'Utente') ? state.settings.displayName : '';
    const base = hour < 5 ? 'Buonanotte' : hour < 12 ? 'Buongiorno' : hour < 18 ? 'Buon pomeriggio' : 'Buonasera';
    return name ? `${base}, ${name}` : base;
  }
  function setupNeeds() {
    const status = state.status || {}; if (!status.ollama_running || status.engine !== 'ollama') return [];
    const installed = status.available_models || []; const wanted = ['qwen3:1.7b']; if (status.recommended_model) wanted.push(status.recommended_model);
    return wanted.filter(name => !installed.includes(name));
  }
  const MODEL_GB = { 'qwen3:1.7b': 1.4, 'qwen3:4b': 2.6, 'qwen3:8b': 5.2 };
  function renderSetupCard() {
    const card = $('#setupCard'); if (!card) return;
    const needs = state.setupRunning ? state.setupQueue : setupNeeds(); const status = state.status || {};
    const show = (state.setupRunning || (needs.length && !state.settings.setupDismissed)) && !el.welcome.classList.contains('hidden');
    card.classList.toggle('hidden', !show); if (!show) return;
    const gb = needs.reduce((sum, name) => sum + (MODEL_GB[name] || 2), 0).toFixed(1).replace('.', ',');
    const none = !(status.available_models || []).length;
    $('#setupTitle').textContent = none ? 'Un ultimo passaggio per iniziare' : 'Prepara Avora al massimo';
    $('#setupText').textContent = state.setupRunning ? 'Download in corso: puoi continuare a usare Avora quando il primo modello è pronto.' : `Scarico automaticamente ${needs.length > 1 ? 'i modelli adatti' : 'il modello adatto'} al tuo computer (${gb} GB in totale, una volta sola). Poi Avora sceglie da sola il più adatto a ogni richiesta.`;
    $('#setupStart').classList.toggle('hidden', state.setupRunning); $('#setupDismiss').classList.toggle('hidden', state.setupRunning || none);
  }
  async function startAutoSetup() {
    const needs = setupNeeds(); if (!needs.length) return;
    state.setupQueue = needs.slice(); state.setupRunning = true; renderSetupCard(); $('#setupProgress').classList.remove('hidden');
    for (const model of needs) {
      try { await api('/api/models/pull', { method: 'POST', body: JSON.stringify({ model }) }); }
      catch (error) { toast(error.message); break; }
      for (;;) {
        const pull = (await api('/api/models/pull')).pull || {}; state.pull = pull;
        const percent = Number.isFinite(pull.percent) ? pull.percent : 0;
        $('#setupBar').style.width = `${percent}%`; $('#setupDetail').textContent = `${pull.model || model} · ${percent}%${pull.detail ? ` · ${pull.detail}` : ''}`;
        if (!pull.active) { if (pull.phase === 'error') { toast(pull.detail || 'Download non riuscito.'); state.setupQueue = []; } break; }
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      state.setupQueue = state.setupQueue.filter(name => name !== model); await refreshStatus();
      if (!state.setupQueue.length && (state.pull || {}).phase === 'error') break;
    }
    state.setupRunning = false; state.setupQueue = []; $('#setupProgress').classList.add('hidden'); await refreshStatus(); renderSetupCard();
    if (!setupNeeds().length) toast('Avora è pronta.');
  }
  // ---- First-run onboarding ----
  const OB_KEY = 'avora-onboarded'; let obStep = 0; let obTimer = null;
  function obSeen() { try { return localStorage.getItem(OB_KEY) === '1'; } catch { return true; } }
  function showOnboarding() { obStep = 0; $('#onboarding').classList.remove('hidden'); document.body.style.overflow = 'hidden'; $('#obName').value = (state.settings.displayName && state.settings.displayName !== 'Utente') ? state.settings.displayName : ''; syncObTheme(); goOb(0); }
  function closeOnboarding() { clearInterval(obTimer); try { localStorage.setItem(OB_KEY, '1'); } catch { /* storage unavailable */ } const layer = $('#onboarding'); layer.classList.add('leaving'); setTimeout(() => { layer.classList.add('hidden'); layer.classList.remove('leaving'); document.body.style.overflow = ''; }, 320); el.input.focus(); }
  function goOb(index) {
    obStep = index; $$('#onboarding .ob-step').forEach(node => { const on = Number(node.dataset.ob) === index; node.classList.toggle('hidden', !on); if (on) { node.classList.remove('ob-in'); void node.offsetWidth; node.classList.add('ob-in'); } });
    $$('#obDots span').forEach((dot, i) => dot.classList.toggle('on', i <= index));
    clearInterval(obTimer); if (index === 2) { void refreshObEngine(); obTimer = setInterval(() => { if (!state.setupRunning) void refreshObEngine(); }, 3000); }
    if (index === 1) setTimeout(() => $('#obName').focus(), 250);
  }
  function syncObTheme() { const choice = state.settings.theme || 'auto'; $$('[data-ob-theme]').forEach(card => { const on = card.dataset.obTheme === choice; card.classList.toggle('active', on); card.setAttribute('aria-checked', String(on)); }); }
  async function refreshObEngine() {
    try { await refreshStatus(); } catch { /* offline */ }
    const status = state.status || {}; const needs = setupNeeds(); const show = (id, on) => $(id).classList.toggle('hidden', !on);
    const set = (dot, stateName) => { $(dot).dataset.state = stateName; };
    if (status.demo) { $('#obEngineText').textContent = 'Modalità demo attiva: le risposte sono di esempio e non serve alcun modello.'; $('#obEngineState').textContent = 'Demo'; $('#obModelState').textContent = 'Non necessario'; set('#obDotEngine', 'ok'); set('#obDotModel', 'ok'); show('#obGetOllama', false); show('#obRecheck', false); show('#obInstall', false); show('#obNext2', true); show('#obSkip', false); return; }
    if (!status.ollama_running) {
      $('#obEngineText').textContent = 'Avora usa Ollama, un motore gratuito che esegue i modelli sul tuo computer. Installalo una sola volta, poi torna qui.'; $('#obEngineState').textContent = 'Non trovato'; $('#obModelState').textContent = 'In attesa del motore'; set('#obDotEngine', 'warn'); set('#obDotModel', 'idle');
      show('#obGetOllama', true); show('#obRecheck', true); show('#obInstall', false); show('#obNext2', false); return;
    }
    set('#obDotEngine', 'ok'); $('#obEngineState').textContent = 'Attivo'; show('#obGetOllama', false); show('#obRecheck', false);
    if (state.setupRunning) { show('#obInstall', false); return; }
    if (needs.length) {
      const gb = needs.reduce((sum, name) => sum + (MODEL_GB[name] || 2), 0).toFixed(1).replace('.', ',');
      $('#obEngineText').textContent = `Un solo clic: Avora scarica i modelli adatti al tuo computer (${gb} GB, una volta sola) e poi sceglie da sola quello giusto per ogni richiesta.`;
      $('#obModelState').textContent = `Da scaricare: ${needs.join(', ')}`; set('#obDotModel', 'warn'); show('#obInstall', true); show('#obNext2', (status.available_models || []).length > 0);
    } else { $('#obEngineText').textContent = 'Tutto è già installato: Avora è pronta all\'uso.'; $('#obModelState').textContent = (status.available_models || []).join(', '); set('#obDotModel', 'ok'); show('#obInstall', false); show('#obNext2', true); show('#obSkip', false); }
  }
  async function obInstall() {
    $('#obInstall').classList.add('hidden'); $('#obProgress').classList.remove('hidden'); $('#obDotModel').dataset.state = 'busy';
    const mirror = setInterval(() => { $('#obBar').style.width = $('#setupBar').style.width || '0%'; $('#obProgressText').textContent = $('#setupDetail').textContent; }, 300);
    try { await startAutoSetup(); } finally { clearInterval(mirror); $('#obProgress').classList.add('hidden'); await refreshObEngine(); }
  }
  async function sendMessage(text, options = {}) {
    if (state.sending) return null;
    const typed = (typeof text === 'string' ? text : el.input.value).trim();
    const files = state.selectedFiles.slice();
    if (!typed && !state.selectedImages.length && !files.length) return null;
    let message = typed || (state.selectedImages.length ? 'Analizza questa immagine.' : 'Analizza questo file.');
    if (files.length) {
      let budget = 11800 - message.length;
      const parts = [];
      for (const file of files) {
        const room = Math.max(0, budget - file.name.length - 40); if (room < 200) { toast('Troppo testo allegato: rimuovi un file o accorcia il messaggio.'); return null; }
        const body = file.text.length > room ? `${file.text.slice(0, room)}\n[... contenuto troncato ...]` : file.text;
        parts.push(`File allegato: ${file.name}\n\`\`\`\n${body}\n\`\`\``); budget -= body.length + file.name.length + 40;
      }
      message += `\n\n${parts.join('\n\n')}`;
    }
    const speaking = Boolean(options.voice || state.settings.autoReadResponses);
    if (speaking) ensureAudioContext();
    const imagesForPayload = state.selectedImages.map(item => ({ name: item.name, mime: item.mime, data: item.data }));
    const imageRequest = !imagesForPayload.length && !files.length && detectImageRequest(typed);
    if (imageRequest) await ensureImageConsent();
    if (!el.welcome.classList.contains('hidden')) showConversation();
    const requestViewEpoch = state.viewEpoch; const requestConversationId = state.conversationId;
    const research = !imageRequest && !files.length && (state.deepResearch || detectWebRequest(typed));
    const optimistic = { role: 'user', content: message, created_at: new Date().toISOString(), attachments: state.selectedImages.map(item => ({ name: item.name, localPreview: item.preview })) };
    const optimisticNode = animateIn(renderMessage(optimistic)); el.messages.append(optimisticNode);
    el.input.value = ''; state.selectedImages = []; state.selectedFiles = []; renderAttachments(); resizeInput(); updateCharCount(); scrollToBottom();
    const controller = new AbortController(); state.abort = controller; setBusy(true);
    const typing = createProcessingMessage(research, imagesForPayload.length);
    if (imageRequest) { const detail = typing.querySelector('.processing-detail'); if (detail) detail.textContent = 'Creo l’immagine richiesta…'; const heading = typing.querySelector('.processing-head strong'); if (heading) heading.textContent = 'Generazione immagine'; }
    el.messages.append(typing); scrollToBottom(); state.progressStartedAt = Date.now(); void pollProgress(typing);
    const speaker = speaking ? createSpeechStream({}) : null; state.lastSpeaker = speaker;
    let live = null; let liveContent = null; let buffer = ''; let frame = 0;
    const render = () => { frame = 0; if (!liveContent) return; const stick = nearBottom(); liveContent.innerHTML = markdownLite(buffer); if (stick) scrollToBottom(); };
    const onDelta = chunk => {
      if (!chunk) return;
      if (!live) { typing.remove(); live = animateIn(renderMessage({ role: 'assistant', content: '' })); live.classList.add('streaming'); liveContent = live.querySelector('.message-content'); el.messages.append(live); }
      buffer += chunk; if (speaker) speaker.push(chunk);
      if (!frame) frame = requestAnimationFrame(render);
    };
    try {
      let result;
      if (imageRequest) {
        result = await api('/api/images/generate-chat', { method: 'POST', signal: controller.signal, body: JSON.stringify({ conversation_id: requestConversationId, message }) });
      } else {
        result = await readChatStream({ conversation_id: requestConversationId, message, images: imagesForPayload, think: state.think, reasoning: state.settings.reasoning || 'medium', math_request: detectMathRequest(typed), deep_research: research, custom_instructions: state.settings.customInstructions || '', response_style: state.settings.responseStyle || 'balanced', voice_mode: Boolean(options.voice), agent: needsAgent(typed) && !options.voice, persona: state.settings.persona || 'general', persona_prompt: state.settings.personaPrompt || '' }, controller.signal, onDelta, event => showToolEvent(typing, event));
      }
      if (frame) cancelAnimationFrame(frame);
      typing.remove();
      const answer = String((result.assistant_message || {}).content || '');
      if (speaker) { if (answer.startsWith(buffer)) speaker.push(answer.slice(buffer.length)); else if (!buffer) speaker.push(answer); speaker.end(); }
      if (requestViewEpoch === state.viewEpoch) {
        state.conversationId = result.conversation_id;
        el.messages.querySelectorAll('.processing-message, .message.streaming').forEach(node => node.remove());
        el.messages.append(renderMessage(result.assistant_message, result.mode)); showConversation();
        await refreshHistory(); renderHistory(); await refreshUsage(); scrollToBottom(); updateContextMeter(result.metrics && result.metrics.completion_tokens);
      } else { await refreshHistory(); }
      if (state.deepResearch) setComposerMode('deepResearch', false);
      return answer;
    } catch (error) {
      if (frame) cancelAnimationFrame(frame);
      typing.remove();
      if (speaker) speaker.cancel();
      if (error.name === 'AbortError') {
        if (live && requestViewEpoch === state.viewEpoch) { live.classList.remove('streaming'); const note = document.createElement('p'); note.className = 'interrupted-note'; note.textContent = 'Generazione interrotta.'; live.querySelector('.message-main').insertBefore(note, live.querySelector('.message-tools')); }
        else { if (optimisticNode.isConnected) optimisticNode.remove(); if (typed && !el.input.value) { el.input.value = typed; resizeInput(); updateCharCount(); } }
        return null;
      }
      if (error.code === 'vision_model_missing') {
        if (optimisticNode.isConnected) optimisticNode.remove();
        state.selectedImages = imagesForPayload.map(item => ({ ...item, preview: `data:${item.mime};base64,${item.data}` })); state.selectedFiles = files; renderAttachments();
        if (typed && !el.input.value) { el.input.value = typed; resizeInput(); updateCharCount(); }
        const visionName = (state.status && state.status.vision_model) || 'qwen3-vl:2b';
        if (confirm(`Per leggere le foto serve il modello visivo ${visionName} (circa 2 GB, installazione automatica). Installarlo ora?`)) { openSettings('model'); void startPull(visionName, 'vision'); }
        return null;
      }
      if (error.code === 'image_provider_not_configured' && requestViewEpoch === state.viewEpoch) {
        if (optimisticNode.isConnected) optimisticNode.remove();
        state.pendingImageMessage = { message: typed, conversationId: requestConversationId };
        $('#imagePrompt').value = typed; openFeature('imageGenLayer');
        setFeatureStatus('imageGenStatus', error.message || 'Installa il modello immagini locale; il download richiede diversi GB.', false);
        await refreshGeneratedImages(); return null;
      }
      if (live) live.remove();
      if (optimisticNode.isConnected) optimisticNode.remove();
      if (requestViewEpoch === state.viewEpoch) { el.messages.querySelectorAll('.processing-message').forEach(node => node.remove()); if (typed && !el.input.value) { el.input.value = typed; resizeInput(); updateCharCount(); } }
      if (String(error.message).includes('limite')) await refreshUsage();
      toast(error.message || 'Richiesta non completata'); return null;
    } finally {
      typing.remove(); if (live) live.classList.remove('streaming');
      if (requestViewEpoch === state.viewEpoch) el.messages.querySelectorAll('.processing-message').forEach(node => node.remove());
      state.abort = null; setBusy(false); if (!options.voice) el.input.focus();
    }
  }
  function resizeInput() { el.input.style.height = 'auto'; el.input.style.height = `${Math.min(el.input.scrollHeight, 170)}px`; }
  function updateCharCount() { $('#charCount').textContent = `${el.input.value.length.toLocaleString('it-IT')} / 12000`; }
  function closeSidebar() { el.sidebar.classList.remove('open'); }
  function newChat() { showWelcome(); el.input.value = ''; resizeInput(); updateCharCount(); }
  function openSettings(tab = 'account') {
    state.panelOpen = true; closeProjects(); el.panel.classList.remove('hidden'); el.overlay.classList.remove('hidden'); document.body.style.overflow = 'hidden'; selectSettingsTab(tab); refreshStatus(); refreshUsage();
  }
  function closeSettings() { state.panelOpen = false; el.panel.classList.add('hidden'); if (!state.projectsOpen) el.overlay.classList.add('hidden'); document.body.style.overflow = state.projectsOpen ? 'hidden' : ''; }
  function selectSettingsTab(tab) {
    $$('.settings-tab').forEach(button => button.classList.toggle('active', button.dataset.tab === tab));
    $$('[data-panel]').forEach(panel => panel.classList.toggle('hidden', panel.dataset.panel !== tab));
  }
  async function renameConversation(conversation) {
    const title = prompt('Nuovo titolo della conversazione:', conversation.title || 'Nuova conversazione');
    if (title === null) return; if (!title.trim()) { toast('Il titolo non può essere vuoto'); return; }
    try { await api(`/api/conversations/${conversation.id}`, { method: 'PATCH', body: JSON.stringify({ title: title.trim().slice(0, 90) }) }); await refreshHistory(); toast('Conversazione rinominata'); }
    catch (error) { toast(error.message); }
  }
  async function deleteConversation(conversation) {
    if (state.settings.confirmDelete !== false && !confirm(`Eliminare la conversazione “${conversation.title || 'Nuova conversazione'}”?`)) return;
    try { await api(`/api/conversations/${conversation.id}`, { method: 'DELETE' }); if (state.conversationId === conversation.id) newChat(); await refreshHistory(); toast('Conversazione eliminata'); }
    catch (error) { toast(error.message); }
  }
  function downloadFile(filename, content, type = 'text/plain;charset=utf-8') {
    const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function exportConversation() {
    if (!state.conversationId) return;
    try {
      const data = await api(`/api/conversations/${state.conversationId}`); const conversation = data.conversation || {};
      const body = [`# ${conversation.title || 'Conversazione Avora'}`, '', ...(data.messages || []).flatMap(m => [`## ${m.role === 'user' ? (state.settings.displayName || 'Utente') : 'Avora'}`, '', m.content, ''])].join('\n');
      downloadFile(`${safeFilename(conversation.title || 'conversazione')}.md`, body); toast('Conversazione esportata');
    } catch (error) { toast(error.message); }
  }
  async function exportAll() {
    try {
      const list = await api('/api/conversations'); const conversations = await Promise.all((list.conversations || []).map(async item => ({ conversation: item, messages: (await api(`/api/conversations/${item.id}`)).messages || [] })));
      downloadFile('avora-cronologia.json', JSON.stringify({ exported_at: new Date().toISOString(), app: 'Avora', conversations }, null, 2), 'application/json;charset=utf-8'); toast('Cronologia esportata');
    } catch (error) { toast(`Esportazione non riuscita: ${error.message}`); }
  }
  function safeFilename(value) { return String(value).normalize('NFKD').replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 70) || 'conversazione'; }
  async function deleteAll() {
    if (!state.conversations.length) { toast('La cronologia è già vuota'); return; }
    if (state.settings.confirmDelete !== false && !confirm(`Eliminare tutte le ${state.conversations.length} conversazioni salvate su questo dispositivo? L'operazione non può essere annullata.`)) return;
    try {
      const snapshot = [...state.conversations];
      for (const conversation of snapshot) await api(`/api/conversations/${conversation.id}`, { method: 'DELETE' });
      newChat(); await refreshHistory(); toast('Cronologia eliminata'); closeSettings();
    } catch (error) { toast(`Eliminazione incompleta: ${error.message}`); await refreshHistory(); }
  }
  function applyAppearance() {
    const root = document.documentElement; const choice = state.settings.theme || 'system';
    const dark = choice === 'dark' || (choice === 'system' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
    root.dataset.theme = dark ? 'dark' : 'light'; root.dataset.textSize = state.settings.textSize || 'normal';
    $$('[data-theme-choice]').forEach(button => { const on = button.dataset.themeChoice === choice; button.classList.toggle('active', on); button.setAttribute('aria-checked', String(on)); });
    $$('[data-size-choice]').forEach(button => { const on = button.dataset.sizeChoice === (state.settings.textSize || 'normal'); button.classList.toggle('active', on); button.setAttribute('aria-checked', String(on)); });
    const meta = document.querySelector('meta[name="theme-color"]'); if (meta) meta.setAttribute('content', dark ? '#121212' : '#ffffff');
  }
  function loadPreferences() {
    try { state.settings = JSON.parse(localStorage.getItem('clara-preferences') || '{}'); } catch { state.settings = {}; }
    state.settings.displayName = state.settings.displayName || 'Utente'; state.settings.enterToSend = state.settings.enterToSend !== false; state.settings.compactMode = Boolean(state.settings.compactMode); state.settings.confirmDelete = state.settings.confirmDelete !== false;
    state.settings.profileEmail = state.settings.profileEmail || ''; state.settings.customInstructions = state.settings.customInstructions || ''; state.settings.responseStyle = state.settings.responseStyle || 'balanced';
    state.settings.voiceName = state.settings.voiceName || ''; state.settings.voiceRate = state.settings.voiceRate || '1.05'; state.settings.voiceEngine = state.settings.voiceEngine === 'system' ? 'system' : 'natural'; state.settings.systemVoiceName = state.settings.systemVoiceName || ''; state.settings.persona = state.settings.persona || 'general'; state.settings.personaPrompt = state.settings.personaPrompt || ''; state.settings.agent = Boolean(state.settings.agent); state.settings.theme = ['light', 'dark', 'system'].includes(state.settings.theme) ? state.settings.theme : 'system'; state.settings.textSize = ['small', 'normal', 'large'].includes(state.settings.textSize) ? state.settings.textSize : 'normal'; state.settings.autoReadResponses = Boolean(state.settings.autoReadResponses);
    el.displayName.value = state.settings.displayName; el.enterToSend.checked = state.settings.enterToSend; el.compactMode.checked = state.settings.compactMode; $('#confirmDelete').checked = state.settings.confirmDelete;
    $('#profileEmail').value = state.settings.profileEmail; $('#customInstructions').value = state.settings.customInstructions; $('#responseStyle').value = state.settings.responseStyle;
    $('#voiceRate').value = String(state.settings.voiceRate); $('#autoReadResponses').checked = state.settings.autoReadResponses; $('#voiceEngine').value = state.settings.voiceEngine;
    populateVoiceOptions(); $('#personaCustom').value = state.settings.personaPrompt; 
    document.body.classList.toggle('compact-mode', state.settings.compactMode); applyAppearance(); updateProfile();
    try { state.projects = JSON.parse(localStorage.getItem('clara-projects') || '[]'); if (!Array.isArray(state.projects)) state.projects = []; } catch { state.projects = []; }
    renderProjects();
  }
  function persistPreferences() {
    try { localStorage.setItem('clara-preferences', JSON.stringify(state.settings)); return true; } catch { toast('Impossibile salvare nel browser: lo spazio potrebbe essere esaurito.'); return false; }
  }
  function savePreferences() {
    state.settings.displayName = el.displayName.value.trim().slice(0, 40) || 'Utente'; state.settings.profileEmail = el.profileEmail.value.trim().slice(0, 140); state.settings.enterToSend = el.enterToSend.checked; state.settings.compactMode = el.compactMode.checked; state.settings.confirmDelete = $('#confirmDelete').checked;
    if (state.settings.profileEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(state.settings.profileEmail)) { toast('Controlla il formato dell’email.'); return; }
    persistPreferences(); document.body.classList.toggle('compact-mode', state.settings.compactMode); updateProfile(); toast('Profilo e preferenze salvati su questo browser');
  }
  function savePersonalization() {
    state.settings.customInstructions = $('#customInstructions').value.trim().slice(0, 3000); state.settings.responseStyle = $('#responseStyle').value; state.settings.personaPrompt = $('#personaCustom').value.trim().slice(0, 2000); persistPreferences(); toast('Personalizzazione salvata');
  }
  async function compressImage(file, maxSize = 320) {
    if (!file.type.startsWith('image/')) throw new Error('Seleziona un file immagine.');
    if (file.size > 8 * 1024 * 1024) throw new Error('L’immagine deve essere inferiore a 8 MB.');
    const dataUrl = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error('L’immagine non può essere letta.')); reader.readAsDataURL(file); });
    const img = new Image(); img.src = dataUrl;
    await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = () => reject(new Error('Formato immagine non valido.')); });
    const scale = Math.min(1, maxSize / Math.max(img.width, img.height)); const canvas = document.createElement('canvas'); canvas.width = Math.max(1, Math.round(img.width * scale)); canvas.height = Math.max(1, Math.round(img.height * scale));
    const ctx = canvas.getContext('2d'); ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.82);
  }
  async function handleAvatar(file) {
    if (!file) return;
    try { state.settings.avatarData = await compressImage(file, 320); persistPreferences(); updateProfile(); toast('Immagine del profilo aggiornata'); }
    catch (error) { toast(error.message); }
  }
  function setComposerMode(kind, enabled) {
    if (kind === 'think') state.think = enabled; else state.deepResearch = enabled;
    const button = kind === 'think' ? $('#thinkToggle') : $('#researchToggle'); button.classList.toggle('active', enabled); button.setAttribute('aria-pressed', String(enabled));
    if (enabled && kind === 'deepResearch') toast('Esplora attivo: la prossima richiesta proverà a cercare fonti online.');
    else if (enabled && kind === 'think') toast('Pensa attivo: il modello proverà a dedicare più ragionamento alla risposta.');
  }
  function renderAttachments() {
    const wrap = $('#attachmentPreview'); wrap.replaceChildren(); wrap.classList.toggle('hidden', !state.selectedImages.length && !state.selectedFiles.length);
    state.selectedImages.forEach((item, index) => {
      const card = document.createElement('div'); card.className = 'attachment-card'; const img = document.createElement('img'); img.src = item.preview; img.alt = item.name; const label = document.createElement('span'); label.textContent = item.name; const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'attachment-remove'; remove.textContent = '×'; remove.setAttribute('aria-label', `Rimuovi ${item.name}`); remove.addEventListener('click', () => { state.selectedImages.splice(index, 1); renderAttachments(); }); card.append(img, label, remove); wrap.append(card);
    });
    state.selectedFiles.forEach((item, index) => {
      const card = document.createElement('div'); card.className = 'attachment-card is-file'; const icon = document.createElement('span'); icon.className = 'attachment-file-icon'; icon.innerHTML = ICONS.fileText; const label = document.createElement('span'); label.textContent = item.name; const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'attachment-remove'; remove.textContent = '×'; remove.setAttribute('aria-label', `Rimuovi ${item.name}`); remove.addEventListener('click', () => { state.selectedFiles.splice(index, 1); renderAttachments(); }); card.append(icon, label, remove); wrap.append(card);
    });
  }
  $('#attachmentPreview').addEventListener('click', event => {
    if (event.target.closest('.attachment-remove')) return; const card = event.target.closest('.attachment-card'); if (!card) return;
    const cards = [...$('#attachmentPreview').children]; const i = cards.indexOf(card);
    if (i < state.selectedImages.length) openFilePreview(state.selectedImages[i], true); else openFilePreview(state.selectedFiles[i - state.selectedImages.length], false);
  });
  $('#closeFilePreview').addEventListener('click', closeFilePreview); $('#filePreviewLayer').addEventListener('click', event => { if (event.target.id === 'filePreviewLayer') closeFilePreview(); });
  $('#promptAdd').addEventListener('click', () => { const title = $('#promptTitle').value.trim(); const body = $('#promptBody').value.trim(); if (!title || !body) { toast('Inserisci titolo e testo del prompt.'); return; } state.settings.prompts = [...(state.settings.prompts || []), { title, body }].slice(0, 30); persistPreferences(); $('#promptTitle').value = ''; $('#promptBody').value = ''; renderPromptList(); toast('Prompt aggiunto.'); });
  $('#obStart').addEventListener('click', () => goOb(1));
  $$('#onboarding [data-ob-back]').forEach(b => b.addEventListener('click', () => goOb(Math.max(0, obStep - 1))));
  $('#obNext1').addEventListener('click', () => { const name = $('#obName').value.trim(); if (name) { state.settings.displayName = name.slice(0, 40); persistPreferences(); updateProfile(); const hello = $('#welcomeHello'); if (hello) hello.textContent = greetingText(); } goOb(2); });
  $('#obName').addEventListener('keydown', event => { if (event.key === 'Enter') $('#obNext1').click(); });
  $$('[data-ob-theme]').forEach(card => card.addEventListener('click', () => { state.settings.theme = card.dataset.obTheme; persistPreferences(); applyAppearance(); syncObTheme(); }));
  $('#obRecheck').addEventListener('click', () => void refreshObEngine()); $('#obInstall').addEventListener('click', () => void obInstall());
  $('#obNext2').addEventListener('click', () => goOb(3)); $('#obSkip').addEventListener('click', () => goOb(3));
  $$('.ob-idea').forEach(b => b.addEventListener('click', () => { closeOnboarding(); el.input.value = b.dataset.idea; resizeInput(); updateCharCount(); }));
  $('#obFinish').addEventListener('click', closeOnboarding);
  const replay = $('#replayOnboarding'); if (replay) replay.addEventListener('click', () => { closeSettings(); showOnboarding(); });
  const TEXT_FILE_RE = /\.(txt|md|markdown|csv|tsv|json|xml|yaml|yml|toml|ini|log|py|js|mjs|ts|tsx|jsx|html|css|scss|java|c|h|cpp|hpp|cs|go|rs|rb|php|sh|bash|zsh|sql|swift|kt|kts|r|lua|pl|vue|svelte)$/i;
  async function addFiles(fileList) {
    for (const file of [...(fileList || [])]) {
      try {
        if (file.type.startsWith('image/')) {
          if (state.selectedImages.length >= 4) { toast('Puoi allegare al massimo quattro foto per messaggio.'); continue; }
          if (state.status && state.status.ollama_running && state.status.vision_model_loaded === false && !state.visionHinted) { state.visionHinted = true; toast('Per leggere le foto serve il modello visivo: ti proporrò di installarlo all’invio.'); }
          const preview = await compressImage(file, 1600); state.selectedImages.push({ name: file.name || 'immagine', mime: 'image/jpeg', data: preview.split(',')[1], preview });
        } else if (file.type.startsWith('text/') || file.type === 'application/json' || TEXT_FILE_RE.test(file.name || '')) {
          if (file.size > 400 * 1024) { toast(`${file.name}: file troppo grande (massimo 400 KB).`); continue; }
          if (state.selectedFiles.length >= 3) { toast('Puoi allegare al massimo tre file di testo per messaggio.'); continue; }
          state.selectedFiles.push({ name: file.name, text: await file.text() });
        } else toast(`${file.name || 'File'}: formato non supportato. Allega foto, testo o codice.`);
      } catch (error) { toast(error.message || 'Allegato non leggibile.'); }
    }
    renderAttachments();
  }
  function openProjects() { state.projectsOpen = true; $('#projectsPanel').classList.remove('hidden'); el.overlay.classList.remove('hidden'); document.body.style.overflow = 'hidden'; renderProjects(); }
  function closeProjects() { state.projectsOpen = false; $('#projectsPanel').classList.add('hidden'); if (!state.panelOpen) el.overlay.classList.add('hidden'); document.body.style.overflow = state.panelOpen ? 'hidden' : ''; }
  function renderProjects() {
    const target = $('#projectList'); if (!target) return; target.replaceChildren();
    if (!state.projects.length) { const empty = document.createElement('p'); empty.className = 'projects-empty'; empty.textContent = 'Non hai ancora creato progetti.'; target.append(empty); return; }
    state.projects.forEach(project => { const card = document.createElement('article'); card.className = 'project-card'; const title = document.createElement('strong'); title.textContent = project.name; const desc = document.createElement('p'); desc.textContent = project.instructions || 'Nessuna istruzione salvata.'; const actions = document.createElement('div'); actions.className = 'inline-actions'; const use = document.createElement('button'); use.className = 'button-secondary'; use.type = 'button'; use.textContent = 'Usa istruzioni'; use.addEventListener('click', () => { state.settings.customInstructions = project.instructions || ''; $('#customInstructions').value = state.settings.customInstructions; persistPreferences(); closeProjects(); openSettings('personalization'); toast(`Istruzioni di “${project.name}” applicate`); }); const remove = document.createElement('button'); remove.className = 'text-button danger-text'; remove.type = 'button'; remove.textContent = 'Elimina'; remove.addEventListener('click', () => { if (confirm(`Eliminare il progetto “${project.name}”?`)) { state.projects = state.projects.filter(x => x.id !== project.id); localStorage.setItem('clara-projects', JSON.stringify(state.projects)); renderProjects(); } }); actions.append(use, remove); card.append(title, desc, actions); target.append(card); });
  }
  async function refreshUsage() {
    try {
      const data = await api('/api/usage'); const usage = data.usage;
      const percent = Math.min(100, usage.percent_used || 0);
      $('#usagePercent').textContent = `${percent.toLocaleString('it-IT')}%`;
      $('#usageBar').style.width = `${percent}%`;
      $('#usageUsed').textContent = `${usage.tokens_used.toLocaleString('it-IT')} usati · ${usage.remaining_tokens.toLocaleString('it-IT')} rimanenti`;
      const seconds = usage.seconds_until_reset || 0;
      const resetText = seconds ? `Reset tra ${Math.floor(seconds / 3600)} h ${Math.floor((seconds % 3600) / 60)} min` : 'Reset disponibile';
      $('#usageReset').textContent = resetText;
      const descriptions = { free: '300.000 token ogni 3 ore', pro: '1.000.000 token ogni 3 ore', max: '3.000.000 token ogni 3 ore' };
      $('#activePlanName').textContent = usage.plan_name;
      $('#activePlanDescription').textContent = `${descriptions[usage.plan] || descriptions.free}. Il contatore si resetta ogni 3 ore.`;
      $('#activePlanBadge').textContent = 'Attivo';
      $('#usageWindowNote').textContent = 'I token sono letti dalle metriche del modello locale. Il limite è applicato da Avora su questo dispositivo e non comporta alcun costo.';
      $('#quotaSummary').textContent = `Limite ${usage.plan_name} · ${usage.remaining_tokens.toLocaleString('it-IT')} token disponibili · ${resetText.toLowerCase()}`;
      $$('.plan-choice').forEach(button => {
        const current = button.dataset.plan === usage.plan;
        button.disabled = current;
        button.textContent = current ? 'Attivo' : 'Seleziona';
        button.closest('.plan-card')?.classList.toggle('selected-plan', current);
      });
    } catch (error) {
      $('#usageUsed').textContent = 'Utilizzo non disponibile';
      $('#quotaSummary').textContent = 'Contatore token non disponibile';
    }
  }

  const progressPhases = [
    ['validating', 'Verifica della richiesta'], ['context', 'Preparazione del contesto'],
    ['model', 'Connessione al modello locale'], ['searching', 'Ricerca web'], ['sources', 'Raccolta delle fonti'],
    ['thinking', 'Elaborazione del modello'], ['generating', 'Generazione della risposta'],
    ['finalizing', 'Salvataggio e conteggio token'], ['done', 'Completato']
  ];
  function createProcessingMessage(research, imageCount) {
    const wrapper = document.createElement('article'); wrapper.className = 'message assistant processing-message';
    const meta = document.createElement('div'); meta.className = 'message-meta'; const name = document.createElement('strong'); name.textContent = 'Avora'; const time = document.createElement('time'); time.textContent = 'in elaborazione'; meta.append(name, time);
    const card = document.createElement('div'); card.className = 'processing-card';
    const head = document.createElement('div'); head.className = 'processing-head'; const spinner = document.createElement('span'); spinner.className = 'processing-spinner'; const title = document.createElement('strong'); title.dataset.progressTitle = ''; title.textContent = 'Verifica della richiesta'; head.append(spinner, title);
    const detail = document.createElement('p'); detail.className = 'processing-detail'; detail.dataset.progressDetail = ''; detail.textContent = imageCount ? `Preparazione di ${imageCount} immagine/i e del contesto della chat.` : 'Controllo della richiesta e del budget token.';
    const list = document.createElement('ol'); list.className = 'processing-steps'; list.dataset.progressSteps = '';
    const visiblePhases = research ? progressPhases : progressPhases.filter(([phase]) => !['searching','sources'].includes(phase));
    visiblePhases.filter(([phase]) => phase !== 'done').forEach(([phase, label]) => { const li = document.createElement('li'); li.dataset.phase = phase; li.textContent = label; list.append(li); });
    const live = document.createElement('div'); live.className = 'processing-live-output message-content'; live.dataset.liveOutput = ''; live.hidden = true;
    card.append(head, detail, list); wrapper.append(meta, card, live); return wrapper;
  }
  function updateProcessingMessage(node, progress) {
    const title = node.querySelector('[data-progress-title]'); const detail = node.querySelector('[data-progress-detail]');
    if (title) title.textContent = ({ validating: 'Verifica della richiesta', context: 'Preparazione della conversazione', searching: 'Ricerca web in corso', sources: 'Organizzazione delle fonti', model: 'Connessione al modello locale', thinking: 'Elaborazione del modello', generating: 'Generazione della risposta', finalizing: 'Salvataggio dei risultati', done: 'Risposta completata', limited: 'Limite token raggiunto', error: 'Richiesta interrotta' })[progress.phase] || 'Elaborazione';
    if (detail && progress.detail) detail.textContent = progress.detail;
    const order = ['validating','context','model','searching','sources','thinking','generating','finalizing','done']; const current = Math.max(0, order.indexOf(progress.phase));
    node.querySelectorAll('[data-phase]').forEach(li => { const index = order.indexOf(li.dataset.phase); li.classList.toggle('complete', index >= 0 && index < current); li.classList.toggle('current', li.dataset.phase === progress.phase); });
    // The final response is rendered once, in its own message. Never mirror streamed
    // text into the progress card: this created tall duplicate answer blocks in Safari.
    const live = node.querySelector('[data-live-output]');
    if (live) { live.hidden = true; live.replaceChildren(); }
  }
  async function pollProgress(node) {
    while (state.sending && node.isConnected) {
      try { const data = await api('/api/progress'); if (node.isConnected && data.progress) { updateProcessingMessage(node, data.progress); scrollToBottom(); } }
      catch { /* polling failure never blocks chat completion */ }
      await new Promise(resolve => setTimeout(resolve, 450));
    }
  }

  // Voice output: the answer is spoken sentence by sentence while it is still being written.
  // Natural voices use the optional Edge Neural TTS endpoint with one sentence prefetched ahead;
  // the system voice starts instantly and needs no network.
  const voiceAPI = window.speechSynthesis || null;
  const NATURAL_VOICES = [
    { name: 'it-IT-ElsaNeural', label: 'Elsa', lang: 'it-IT' },
    { name: 'it-IT-IsabellaNeural', label: 'Isabella', lang: 'it-IT' },
    { name: 'it-IT-DiegoNeural', label: 'Diego', lang: 'it-IT' },
    { name: 'it-IT-GiuseppeMultilingualNeural', label: 'Giuseppe', lang: 'it-IT' }
  ];
  function populateVoiceOptions() {
    const select = $('#voiceSelect'); if (!select) return;
    select.replaceChildren();
    if (state.settings.voiceEngine === 'system') {
      select.append(new Option('Voce italiana predefinita del sistema', ''));
      const voices = voiceAPI ? voiceAPI.getVoices().filter(voice => /^it([_-]|$)/i.test(voice.lang || '')) : [];
      voices.forEach(voice => select.append(new Option(voice.name, voice.name)));
      select.value = voices.some(voice => voice.name === state.settings.systemVoiceName) ? state.settings.systemVoiceName : '';
    } else {
      NATURAL_VOICES.forEach(voice => select.append(new Option(voice.label, voice.name)));
      select.value = NATURAL_VOICES.some(voice => voice.name === state.settings.voiceName) ? state.settings.voiceName : NATURAL_VOICES[0].name;
    }
  }
  if (voiceAPI) voiceAPI.onvoiceschanged = () => populateVoiceOptions();
  function selectedVoice() {
    const name = state.settings.voiceName || 'it-IT-ElsaNeural';
    return NATURAL_VOICES.find(voice => voice.name === name) || NATURAL_VOICES[0];
  }
  function ensureAudioContext() {
    try {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) return null;
      if (!state.voiceAudioContext) state.voiceAudioContext = new Context();
      if (state.voiceAudioContext.state === 'suspended') void state.voiceAudioContext.resume().catch(() => {});
      return state.voiceAudioContext;
    } catch { return null; }
  }
  function setVoiceVisual(stateName, statusText) {
    const wrap = $('#voiceOrbWrap'); if (wrap) wrap.dataset.state = stateName;
    const status = $('#voiceModeStatus'); if (status && statusText) status.textContent = statusText;
    const button = $('#voiceModeToggle');
    if (button) button.textContent = stateName === 'listening' ? 'Interrompi ascolto' : stateName === 'thinking' ? 'Sto elaborando…' : stateName === 'speaking' ? 'Interrompi audio' : 'Inizia a parlare';
    const orb = $('#voiceOrbButton');
    if (orb) orb.setAttribute('aria-label', stateName === 'listening' ? 'Ferma ascolto' : stateName === 'speaking' ? 'Interrompi audio' : 'Avvia ascolto vocale');
    const icon = $('#voiceOrbButton .voice-orb-icon');
    if (icon) icon.innerHTML = stateName === 'speaking' ? ICONS.volume : stateName === 'thinking' ? ICONS.brain : stateName === 'listening' ? ICONS.stop : ICONS.mic;
  }
  function cleanSpeechText(text) {
    return stripEmojiClient(String(text || '')).replace(/```[\s\S]*?```/g, ' blocco di codice omesso. ').replace(/`([^`]+)`/g, '$1').replace(/`+/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/https?:\/\/\S+/g, ' ').replace(/^\s*\|?[\s:|-]{3,}\|?\s*$/gm, ' ').replace(/\|/g, ', ')
      .replace(/^\s*[-*+]\s+/gm, '').replace(/^\s*\d+[.)]\s+/gm, '').replace(/[#*_>~]/g, '').replace(/\s+/g, ' ').trim();
  }
  function voiceLayerOpen() { const layer = $('#voiceModeLayer'); return Boolean(layer && !layer.classList.contains('hidden')); }
  function finishSpeech(generation, success = true) {
    if (generation !== state.speechGeneration) return;
    state.voiceSpeaking = false; state.voiceAudioSource = null;
    if (state.activeSpeechButton) { state.activeSpeechButton.innerHTML = `${ICONS.volume}<span>Ascolta</span>`; state.activeSpeechButton = null; }
    if (voiceLayerOpen()) setVoiceVisual('idle', state.voiceSessionActive ? 'Tocca a te. Sto riascoltando…' : (success ? 'Lettura terminata.' : 'Audio non disponibile.'));
  }
  function stopSpeaking() {
    state.speechGeneration += 1;
    if (voiceAPI) { try { voiceAPI.cancel(); } catch {} }
    if (state.voiceAudioSource) { try { state.voiceAudioSource.onended = null; state.voiceAudioSource.stop(); } catch {} state.voiceAudioSource = null; }
    if (state.speechResolver) { const pending = state.speechResolver; state.speechResolver = null; try { pending(false); } catch {} }
    if (state.speechFinish) { const finish = state.speechFinish; state.speechFinish = null; try { finish(); } catch {} }
    state.voiceSpeaking = false;
    if (state.activeSpeechButton) { state.activeSpeechButton.innerHTML = `${ICONS.volume}<span>Ascolta</span>`; state.activeSpeechButton = null; }
    if (voiceLayerOpen()) setVoiceVisual('idle', state.voiceSessionActive ? 'Audio interrotto. Premi il cerchio per parlare.' : 'Audio interrotto.');
  }
  function createSpeechStream(options = {}) {
    stopSpeaking();
    const generation = ++state.speechGeneration; const alive = () => generation === state.speechGeneration;
    const useSystem = state.settings.voiceEngine === 'system' || !ensureAudioContext();
    let naturalFailed = false, warned = false, pending = '', fenced = false, count = 0, ended = false, playing = false, finished = false;
    const queue = []; let resolveDone; const done = new Promise(resolve => { resolveDone = resolve; });
    state.speechFinish = () => resolveDone(false);
    state.activeSpeechButton = options.button || null;
    if (options.button) options.button.innerHTML = `${ICONS.stop}<span>Ferma audio</span>`;
    const rate = () => Number($('#voiceRate')?.value || state.settings.voiceRate || 1.05);
    function fetchAudio(text) {
      const context = ensureAudioContext();
      return fetch('/api/tts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, voice: selectedVoice().name, rate: rate() }) })
        .then(response => { if (!response.ok) throw new Error('tts'); return response.arrayBuffer(); })
        .then(raw => context.decodeAudioData(raw.slice(0))).catch(() => null);
    }
    function playBuffer(buffer) {
      const context = ensureAudioContext();
      return new Promise(resolve => {
        const source = context.createBufferSource(); source.buffer = buffer; source.connect(context.destination);
        state.voiceAudioSource = source; state.speechResolver = resolve;
        source.onended = () => { if (state.voiceAudioSource === source) state.voiceAudioSource = null; state.speechResolver = null; resolve(true); };
        try { source.start(0); } catch { state.speechResolver = null; resolve(false); }
      });
    }
    function speakSystem(text) {
      if (!voiceAPI || typeof SpeechSynthesisUtterance === 'undefined') return Promise.resolve(false);
      return new Promise(resolve => {
        const voices = voiceAPI.getVoices();
        const chosen = voices.find(voice => voice.name === state.settings.systemVoiceName) || voices.find(voice => /^it([_-]|$)/i.test(voice.lang || '') && voice.default) || voices.find(voice => /^it([_-]|$)/i.test(voice.lang || '')) || null;
        const utterance = new SpeechSynthesisUtterance(text); utterance.lang = chosen?.lang || 'it-IT'; if (chosen) utterance.voice = chosen; utterance.rate = Math.max(0.8, Math.min(1.3, rate()));
        utterance.onend = () => { state.speechResolver = null; resolve(true); }; utterance.onerror = () => { state.speechResolver = null; resolve(false); };
        state.speechResolver = resolve;
        try { voiceAPI.speak(utterance); } catch { state.speechResolver = null; resolve(false); }
      });
    }
    async function pump() {
      if (playing || finished) return; playing = true; state.voiceSpeaking = true;
      try {
        while (queue.length && alive()) {
          const item = queue.shift(); if (voiceLayerOpen()) setVoiceVisual('speaking', 'Avora sta parlando.');
          let ok = false;
          if (item.audio) {
            const buffer = await item.audio; if (!alive()) break;
            if (buffer) ok = await playBuffer(buffer);
            else { naturalFailed = true; if (!warned) { warned = true; toast('Voce naturale non disponibile: uso la voce di sistema.'); } }
          }
          if (!alive()) break;
          if (!ok && (naturalFailed || !item.audio)) ok = await speakSystem(item.text);
        }
      } finally { playing = false; }
      if (!alive()) { finished = true; resolveDone(false); return; }
      if (ended && !queue.length) { finished = true; finishSpeech(generation, true); resolveDone(true); }
    }
    function emit(text) {
      const clean = cleanSpeechText(text); if (!clean) return;
      queue.push({ text: clean, audio: (useSystem || naturalFailed) ? null : fetchAudio(clean) }); count += 1; void pump();
    }
    function drain(final) {
      for (;;) {
        if (fenced) { const close = pending.indexOf('```'); if (close < 0) { pending = ''; return; } pending = pending.slice(close + 3); fenced = false; emit('blocco di codice omesso.'); continue; }
        const open = pending.indexOf('```');
        if (open >= 0) { const before = pending.slice(0, open); if (before.trim()) emit(before); pending = pending.slice(open + 3); fenced = true; continue; }
        const min = count === 0 ? 25 : 50; let cut = -1; let match; const boundary = /[.!?…:;](?=\s)|\n/g;
        while ((match = boundary.exec(pending))) { if (match.index + 1 >= min) { cut = match.index + 1; break; } }
        if (cut < 0 && count === 0) { const comma = /,(?=\s)/g; while ((match = comma.exec(pending))) { if (match.index >= 45) { cut = match.index + 1; break; } } }
        if (cut < 0 && pending.length > 320) { cut = pending.lastIndexOf(' ', 300); if (cut < 100) cut = 300; }
        if (cut < 0) break;
        emit(pending.slice(0, cut)); pending = pending.slice(cut);
      }
      if (final && pending.trim() && !fenced) { emit(pending); pending = ''; }
    }
    return {
      push(text) { if (!alive() || finished) return; pending += String(text || ''); drain(false); },
      end() { if (!alive() || finished) return; drain(true); ended = true; void pump(); },
      cancel() { if (alive()) stopSpeaking(); },
      done
    };
  }
  async function speakText(text, options = {}) {
    if (!cleanSpeechText(text)) { toast('Non c’è testo da leggere.'); return false; }
    const speaker = createSpeechStream(options); speaker.push(text); speaker.end(); return speaker.done;
  }
  function recognitionConstructor() { return window.SpeechRecognition || window.webkitSpeechRecognition || null; }
  function setTranscript(text) { const target = $('#voiceTranscript'); if (target) target.textContent = text; }
  function startVoiceSession() {
    const Recognition = recognitionConstructor();
    if (!Recognition) { state.voiceSessionActive = false; setVoiceVisual('idle', 'Il riconoscimento vocale non è supportato da questo browser. Usa il dettato di macOS nel campo chat oppure prova un browser compatibile.'); toast('Riconoscimento vocale non disponibile in questo browser.'); return; }
    ensureAudioContext(); state.voiceSessionActive = true; startVoiceListening();
  }
  function startVoiceListening() {
    if (!state.voiceSessionActive || state.voiceListening || state.voiceRecognitionStarting || state.voiceProcessing || state.voiceSpeaking) return;
    const Recognition = recognitionConstructor();
    if (!Recognition) { state.voiceSessionActive = false; setVoiceVisual('idle', 'Riconoscimento vocale non disponibile. Usa il campo di testo o il dettato di macOS.'); return; }
    let recognition;
    try {
      recognition = new Recognition(); state.voiceRecognition = recognition; state.voiceRecognitionStarting = true;
      let finalHandled = false;
      recognition.lang = 'it-IT'; recognition.interimResults = true; recognition.continuous = false; recognition.maxAlternatives = 1;
      recognition.onstart = () => {
        if (state.voiceRecognition !== recognition) return;
        state.voiceRecognitionStarting = false; state.voiceListening = true; setVoiceVisual('listening', 'Ti ascolto. Parla, poi fai una breve pausa.'); setTranscript('Sto ascoltando…');
      };
      recognition.onresult = event => {
        if (state.voiceRecognition !== recognition || finalHandled) return;
        let finalText = ''; let interimText = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i]; if (item.isFinal) finalText += item[0].transcript; else interimText += item[0].transcript;
        }
        const visible = (finalText || interimText).trim(); if (visible) setTranscript(visible);
        if (finalText.trim() && !finalHandled) {
          finalHandled = true; state.voiceProcessing = true; state.voiceListening = false;
          setVoiceVisual('thinking', 'Ho capito. Invio la richiesta a Avora…'); setTranscript(`Tu: ${finalText.trim()}`);
          try { recognition.stop(); } catch {}
          void handleVoicePrompt(finalText.trim());
        }
      };
      recognition.onerror = event => {
        if (state.voiceRecognition !== recognition) return;
        state.voiceListening = false; state.voiceRecognitionStarting = false; state.voiceRecognition = null;
        const messages = { 'not-allowed': 'Permesso microfono negato. Abilitalo nelle impostazioni del browser.', 'service-not-allowed': 'Il browser non autorizza il riconoscimento vocale.', 'no-speech': 'Non ho sentito parole. Premi il cerchio per riprovare.', 'network': 'Il servizio di riconoscimento vocale non è raggiungibile. Riprova tra poco.', 'audio-capture': 'Non trovo un microfono disponibile.' };
        setVoiceVisual('idle', messages[event.error] || `Problema del microfono: ${event.error}.`);
        if (['not-allowed', 'service-not-allowed', 'audio-capture', 'network'].includes(event.error)) state.voiceSessionActive = false;
      };
      // Deliberately do NOT restart recognition here. Auto-restart caused an on/off loop
      // on browsers that emit no-speech/end events repeatedly.
      recognition.onend = () => {
        if (state.voiceRecognition === recognition) { state.voiceRecognition = null; state.voiceListening = false; state.voiceRecognitionStarting = false; }
        if (!state.voiceProcessing && !state.voiceSpeaking && state.voiceSessionActive) setVoiceVisual('idle', 'Ascolto terminato. Premi il cerchio per parlare di nuovo.');
      };
      recognition.start();
    } catch (error) {
      state.voiceListening = false; state.voiceRecognitionStarting = false; state.voiceRecognition = null; state.voiceSessionActive = false;
      setVoiceVisual('idle', `Impossibile avviare il microfono: ${error.message}`);
    }
  }
  async function handleVoicePrompt(text) {
    state.voiceProcessing = true; setTranscript(`Tu: ${text}`); setVoiceVisual('thinking', 'Avora sta scrivendo la risposta…');
    let answer = null;
    try {
      answer = await sendMessage(text, { voice: true });
      if (!state.voiceSessionActive) { if (state.lastSpeaker) state.lastSpeaker.cancel(); return; }
      if (answer) { setTranscript(`Avora: ${answer.replace(/\s+/g, ' ').slice(0, 220)}${answer.length > 220 ? '…' : ''}`); if (state.lastSpeaker) await state.lastSpeaker.done; }
      else setVoiceVisual('idle', 'La richiesta non è riuscita. Premi il cerchio per riprovare.');
    } finally {
      state.voiceProcessing = false;
      if (answer && state.voiceSessionActive && !state.voiceSpeaking) setTimeout(() => startVoiceListening(), 350);
    }
  }
  function stopVoiceListening() {
    const recognition = state.voiceRecognition; state.voiceRecognition = null;
    state.voiceSessionActive = false; state.voiceListening = false; state.voiceRecognitionStarting = false;
    if (recognition) { try { recognition.abort(); } catch { try { recognition.stop(); } catch {} } }
    setVoiceVisual('idle', 'Ascolto in pausa. Premi il cerchio per riprovare.');
  }
  function toggleVoiceInput() {
    ensureAudioContext();
    if (state.voiceSpeaking) { stopSpeaking(); return; }
    if (state.voiceListening || state.voiceRecognitionStarting) { stopVoiceListening(); return; }
    if (!state.voiceSessionActive) state.voiceSessionActive = true;
    startVoiceListening();
  }
  function stopVoiceSession() {
    state.voiceSessionActive = false; state.voiceProcessing = false; state.voiceListening = false; state.voiceRecognitionStarting = false;
    const recognition = state.voiceRecognition; state.voiceRecognition = null;
    if (recognition) { try { recognition.abort(); } catch { try { recognition.stop(); } catch {} } }
    stopSpeaking(); setVoiceVisual('idle', 'Sessione vocale terminata. Premi per riaprirla quando vuoi.');
  }
  function openVoiceMode() {
    populateVoiceOptions(); $('#voiceModeLayer').classList.remove('hidden');
    setVoiceVisual('idle', 'Premi il cerchio e parla. Avora risponde a voce mentre scrive e ti riascolta subito dopo.'); setTranscript('La conversazione riconosciuta apparirà qui.');
    if (!recognitionConstructor()) $('#voiceModeStatus').textContent = 'Questo browser non supporta il microfono vocale. La lettura audio delle risposte resta disponibile.';
  }
  function closeVoiceMode() { stopGeneration(); stopVoiceSession(); $('#voiceModeLayer').classList.add('hidden'); }
  let lastExploreQuery = '';
  function setFeatureStatus(id, message, busy = false) {
    const node = $(`#${id}`); if (!node) return;
    node.textContent = message || ''; node.classList.toggle('hidden', !message);
    node.classList.toggle('is-busy', Boolean(busy));
  }
  function openFeature(id) {
    ['exploreLayer', 'imageGenLayer'].forEach(other => $(`#${other}`).classList.toggle('hidden', other !== id));
    document.body.style.overflow = 'hidden';
  }
  function closeFeatures() {
    $('#exploreLayer').classList.add('hidden'); $('#imageGenLayer').classList.add('hidden'); $('#filePreviewLayer').classList.add('hidden');
    if (!state.panelOpen && !state.projectsOpen && $('#voiceModeLayer').classList.contains('hidden')) document.body.style.overflow = '';
  }
  async function runExploreSearch(query) {
    const normalized = String(query || '').trim();
    if (!normalized) { toast('Scrivi cosa vuoi cercare.'); return; }
    lastExploreQuery = normalized;
    const button = $('#exploreSearchButton'); button.disabled = true; button.textContent = 'Ricerca…';
    setFeatureStatus('exploreStatus', 'Cerco fonti pubbliche…', true);
    const resultsNode = $('#exploreResults'); resultsNode.replaceChildren();
    try {
      const data = await api('/api/search', { method: 'POST', body: JSON.stringify({ query: normalized }) });
      const results = Array.isArray(data.results) ? data.results : [];
      if (!results.length) {
        const empty = document.createElement('p'); empty.className = 'empty-state'; empty.textContent = 'Nessun risultato disponibile. Prova una ricerca più specifica.'; resultsNode.append(empty);
      } else {
        results.forEach(item => {
          const card = document.createElement('article'); card.className = 'search-result-card';
          const link = document.createElement('a'); link.className = 'search-result-title'; link.href = item.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = item.title || item.url;
          const source = document.createElement('p'); source.className = 'search-result-url'; source.textContent = item.url || '';
          const snippet = document.createElement('p'); snippet.className = 'search-result-snippet'; snippet.textContent = item.snippet || 'Apri la fonte per leggere i dettagli.';
          card.append(link, source, snippet); resultsNode.append(card);
        });
      }
      setFeatureStatus('exploreStatus', `${results.length} risultati trovati per “${normalized}”.`);
      $('#exploreUseQuery').disabled = !results.length;
    } catch (error) {
      setFeatureStatus('exploreStatus', error.message || 'Ricerca non riuscita. Controlla Internet e riprova.');
      const empty = document.createElement('p'); empty.className = 'empty-state'; empty.textContent = 'Non sono stati caricati risultati.'; resultsNode.append(empty);
      $('#exploreUseQuery').disabled = true;
    } finally { button.disabled = false; button.textContent = 'Cerca'; }
  }
  function renderImageGallery() {
    const gallery = $('#imageGallery'); gallery.replaceChildren();
    const all = Array.isArray(state.imageGalleryItems) ? state.imageGalleryItems : [];
    const filtered = all.filter(item => state.imageGalleryFilter === 'all' || item.kind === state.imageGalleryFilter);
    if (!filtered.length) {
      const empty = document.createElement('p'); empty.className = 'empty-state';
      empty.textContent = state.imageGalleryFilter === 'generated' ? 'Non hai ancora creato immagini.' : (state.imageGalleryFilter === 'uploaded' ? 'Non hai ancora caricato immagini o allegato foto alle chat.' : 'Qui appariranno tutte le immagini create e caricate.');
      gallery.append(empty); return;
    }
    filtered.forEach(item => {
      const card = document.createElement('article'); card.className = 'generated-image-card';
      const img = document.createElement('img'); img.src = item.url; img.alt = item.prompt || item.filename || 'Immagine nella libreria'; img.loading = 'lazy';
      const source = document.createElement('span'); source.className = `gallery-source ${item.kind === 'generated' ? 'is-generated' : 'is-uploaded'}`; source.textContent = item.kind === 'generated' ? 'Creata' : 'Caricata';
      const caption = document.createElement('p'); caption.textContent = item.prompt || item.filename || 'Immagine';
      const actions = document.createElement('div'); actions.className = 'generated-image-actions';
      const open = document.createElement('a'); open.href = item.url; open.target = '_blank'; open.rel = 'noopener noreferrer'; open.textContent = 'Apri';
      const download = document.createElement('a'); download.href = item.url; download.download = item.filename || 'avora-image'; download.textContent = 'Salva';
      actions.append(open, download); card.append(img, source, caption, actions); gallery.append(card);
    });
  }

  async function refreshGeneratedImages() {
    try {
      const data = await api('/api/images'); const generator = data.generator || {};
      state.imageProviderAvailable = Boolean(generator.available || generator.diagram_available);
      state.imageGalleryItems = Array.isArray(data.gallery) ? data.gallery : [ ...(data.images || []), ...(data.uploads || []) ];
      $('#imageProviderStatusHeading').textContent = generator.local_model_installed ? 'Generatore immagini locale pronto' : (generator.configured ? 'Generatore online configurato' : 'Generatore locale non installato');
      $('#imageProviderStatusText').textContent = generator.reason || 'Verifica del generatore completata.';
      $('#imageLocalInstallWrap').classList.toggle('hidden', Boolean(generator.local_model_installed));
      $('#installLocalImageModel').disabled = Boolean(generator.install?.active);
      $('#installLocalImageModel').textContent = generator.install?.active ? 'Installazione in corso…' : (generator.local_model_installed ? 'Modello installato' : `Installa ${generator.local_model || 'il modello immagini'} · diversi GB`);
      const installProgress = $('#imageInstallProgress');
      installProgress.classList.toggle('hidden', !generator.install?.active && generator.install?.phase !== 'error');
      installProgress.textContent = generator.install?.detail || '';
      $('#generateImageButton').disabled = !state.imageProviderAvailable;
      const hordeToggle = $('#hordeToggle'); if (hordeToggle) hordeToggle.checked = Boolean(generator.horde_enabled);
      renderImageGallery();
    } catch (error) {
      state.imageProviderAvailable = false; $('#generateImageButton').disabled = true;
      $('#imageProviderStatusHeading').textContent = 'Generatore non raggiungibile';
      $('#imageProviderStatusText').textContent = error.message || 'Non riesco a leggere la libreria immagini.';
      $('#imageLocalInstallWrap').classList.remove('hidden');
      renderImageGallery();
      setFeatureStatus('imageGenStatus', error.message || 'Non riesco a leggere la galleria.');
    }
  }

  async function installLocalImageModel() {
    const button = $('#installLocalImageModel');
    if (!confirm('Scaricare il modello immagini tramite Ollama? Occupa diversi GB, richiede spazio e memoria aggiuntivi e il download può richiedere tempo. Nessun pagamento viene eseguito.')) return;
    button.disabled = true; button.textContent = 'Avvio download…';
    const progress = $('#imageInstallProgress'); progress.classList.remove('hidden'); progress.textContent = 'Avvio il download del modello immagini…';
    try {
      const start = await api('/api/images/install-local', { method: 'POST', body: JSON.stringify({}) });
      const initial = start.install || {};
      if (initial.phase === 'error') throw new Error(initial.detail || 'Non è stato possibile avviare il download.');
      state.imageInstallPolling = true;
      while (state.imageInstallPolling) {
        const status = await api('/api/images/install-status');
        const install = status.install || {};
        progress.classList.remove('hidden'); progress.textContent = install.detail || 'Installazione in corso…';
        button.textContent = install.active ? 'Download in corso…' : 'Installa generatore immagini locale';
        if (!install.active) {
          state.imageInstallPolling = false;
          await refreshGeneratedImages();
          if (install.phase === 'done' && state.pendingImageMessage) {
            const pending = state.pendingImageMessage; state.pendingImageMessage = null;
            if (pending.conversationId === state.conversationId || pending.conversationId === null) {
              closeFeatures(); el.input.value = pending.message; await sendMessage(pending.message);
            } else toast('Modello immagini installato. Torna alla chat originale e ripeti la richiesta.');
          } else if (install.phase === 'done') {
            setFeatureStatus('imageGenStatus', 'Modello immagini installato. Ora puoi creare foto e illustrazioni dalla chat o da questa libreria.');
          } else {
            setFeatureStatus('imageGenStatus', install.detail || 'Installazione non completata.');
          }
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 1800));
      }
    } catch (error) {
      state.imageInstallPolling = false;
      progress.classList.remove('hidden'); progress.textContent = error.message || 'Installazione non riuscita.';
      await refreshGeneratedImages();
    } finally {
      button.disabled = false;
      if (button.isConnected && !button.textContent.includes('Installa')) button.textContent = 'Installa generatore immagini locale';
    }
  }

  async function uploadImagesToGallery(files) {
    const selected = [...(files || [])];
    if (!selected.length) return;
    const input = $('#imageGalleryUpload'); input.disabled = true;
    setFeatureStatus('imageGenStatus', `Caricamento di ${selected.length} immagin${selected.length === 1 ? 'e' : 'i'}…`, true);
    let uploaded = 0;
    try {
      for (const file of selected) {
        const dataUrl = await compressImage(file, 1800);
        const raw = String(dataUrl).split(',')[1];
        await api('/api/images/upload', { method: 'POST', body: JSON.stringify({ filename: file.name, mime: 'image/jpeg', data: raw }) });
        uploaded += 1;
      }
      setFeatureStatus('imageGenStatus', `${uploaded} immagin${uploaded === 1 ? 'e caricata' : 'i caricate'} nella tua libreria locale.`);
      state.imageGalleryFilter = 'all';
      $$('.gallery-filter').forEach(button => button.classList.toggle('active', button.dataset.galleryFilter === 'all'));
      await refreshGeneratedImages();
    } catch (error) { setFeatureStatus('imageGenStatus', error.message || 'Caricamento non riuscito.'); await refreshGeneratedImages(); }
    finally { input.disabled = false; input.value = ''; }
  }

  async function createGeneratedImage(event) {
    event.preventDefault();
    const prompt = $('#imagePrompt').value.trim(); if (!prompt) { toast('Scrivi una descrizione per l’immagine.'); return; }
    const button = $('#generateImageButton'); button.disabled = true; button.textContent = 'Generazione…';
    setFeatureStatus('imageGenStatus', 'Generazione in corso…', true);
    try {
      const data = await api('/api/images/generate', { method: 'POST', body: JSON.stringify({ prompt, composition: $('#imageComposition').value }) });
      setFeatureStatus('imageGenStatus', 'Immagine creata e salvata nella galleria locale di Avora.');
      await refreshGeneratedImages();
    } catch (error) {
      setFeatureStatus('imageGenStatus', error.message || 'Generazione non riuscita.');
      await refreshGeneratedImages();
    } finally { button.textContent = 'Genera immagine'; button.disabled = !state.imageProviderAvailable; }
  }

  async function choosePlan(plan) {
    try {
      const result = await api('/api/settings/plan', { method: 'POST', body: JSON.stringify({ plan }) });
      await refreshUsage();
      const name = result.usage.plan_name;
      toast(`Limite ${name} attivato.`);
    } catch (error) { toast(error.message); }
  }


  el.newChat.addEventListener('click', newChat); $('#brandHome').addEventListener('click', event => { event.preventDefault(); newChat(); });
  $('#searchToggle').addEventListener('click', () => { el.historySearchWrap.classList.remove('hidden'); el.historySearch.focus(); closeSidebar(); });
  $('#clearSearch').addEventListener('click', () => { el.historySearch.value = ''; renderHistory(); el.historySearch.focus(); });
  $('#exploreAction').addEventListener('click', () => { closeSidebar(); openFeature('exploreLayer'); $('#exploreQuery').focus(); });
  $('#imagesAction').addEventListener('click', () => { closeSidebar(); openFeature('imageGenLayer'); setFeatureStatus('imageGenStatus', ''); void refreshGeneratedImages(); });
  $('#closeExplore').addEventListener('click', closeFeatures); $('#closeImageGen').addEventListener('click', closeFeatures);
  $('#exploreLayer').addEventListener('click', event => { if (event.target === $('#exploreLayer')) closeFeatures(); });
  $('#imageGenLayer').addEventListener('click', event => { if (event.target === $('#imageGenLayer')) closeFeatures(); });
  $('#exploreForm').addEventListener('submit', event => { event.preventDefault(); void runExploreSearch($('#exploreQuery').value); });
  $('#exploreUseQuery').addEventListener('click', () => {
    if (!lastExploreQuery) return;
    closeFeatures(); newChat();
    el.input.value = `Approfondisci questa ricerca usando fonti web e distinguendo i fatti verificati dalle incertezze: ${lastExploreQuery}`;
    setComposerMode('deepResearch', true); resizeInput(); updateCharCount(); el.input.focus();
  });
  $('#imageGenForm').addEventListener('submit', createGeneratedImage);
  $('#refreshImages').addEventListener('click', () => void refreshGeneratedImages());
  $('#installLocalImageModel').addEventListener('click', () => void installLocalImageModel());
  $('#uploadGalleryImages').addEventListener('click', () => $('#imageGalleryUpload').click());
  $('#imageGalleryUpload').addEventListener('change', event => void uploadImagesToGallery(event.target.files));
  $$('.gallery-filter').forEach(button => button.addEventListener('click', () => {
    state.imageGalleryFilter = button.dataset.galleryFilter || 'all';
    $$('.gallery-filter').forEach(item => item.classList.toggle('active', item === button));
    renderImageGallery();
  }));

  $('#imageProviderForm').addEventListener('submit', async event => {
    event.preventDefault();
    const key = $('#imageProviderKey').value.trim();
    if (!key) { toast('Inserisci la chiave privata del provider.'); return; }
    if (!$('#imageProviderConsent').checked) { toast('Conferma prima l’invio dei prompt al provider esterno.'); return; }
    const button = $('#saveImageProviderKey'); button.disabled = true;
    try {
      const result = await api('/api/settings/image-provider', { method: 'POST', body: JSON.stringify({ api_key: key }) });
      $('#imageProviderKey').value = ''; $('#imageProviderConsent').checked = false;
      state.imageProviderAvailable = Boolean(result.configured);
      toast('Chiave salvata localmente su questo Mac.');
      setFeatureStatus('imageGenStatus', 'Configurazione aggiornata.'); await refreshGeneratedImages();
      const pendingImage = state.pendingImageMessage;
      if (pendingImage) {
        state.pendingImageMessage = null;
        closeFeatures();
        if (pendingImage.conversationId === state.conversationId || pendingImage.conversationId === null) {
          el.input.value = pendingImage.message;
          await sendMessage(pendingImage.message);
        } else {
          toast('Chiave salvata. Torna alla chat da cui avevi richiesto l’immagine e ripeti la richiesta.');
        }
      }
    } catch (error) { toast(error.message || 'Non è stato possibile salvare la chiave.'); }
    finally { button.disabled = false; }
  });
  $('#clearImageProviderKey').addEventListener('click', async () => {
    if (!confirm('Rimuovere la chiave immagini salvata su questo Mac?')) return;
    try {
      await api('/api/settings/image-provider', { method: 'POST', body: JSON.stringify({ api_key: '' }) });
      $('#imageProviderKey').value = ''; $('#imageProviderConsent').checked = false;
      state.imageProviderAvailable = false; toast('Chiave rimossa.'); await refreshGeneratedImages();
    } catch (error) { toast(error.message || 'Non è stato possibile rimuovere la chiave.'); }
  });
  $('#projectsAction').addEventListener('click', () => { openProjects(); closeSidebar(); });
  $('#personalizationAction').addEventListener('click', () => { openSettings('personalization'); closeSidebar(); });
  $('#openSettings').addEventListener('click', () => openSettings('account')); $('#headerSettings').addEventListener('click', () => openSettings('account'));
  $('#closeSettings').addEventListener('click', closeSettings); $('#closeProjects').addEventListener('click', closeProjects); el.overlay.addEventListener('click', () => { closeSettings(); closeProjects(); });
  $('#openSidebar').addEventListener('click', () => el.sidebar.classList.add('open')); $('#closeSidebar').addEventListener('click', closeSidebar);
  $('#refreshHistory').addEventListener('click', refreshHistory); el.historySearch.addEventListener('input', renderHistory);
  $$('.settings-tab').forEach(button => button.addEventListener('click', () => { selectSettingsTab(button.dataset.tab); if (button.dataset.tab === 'usage') refreshUsage(); if (button.dataset.tab === 'model') refreshStatus(); }));
  $('#savePreferences').addEventListener('click', savePreferences); $('#saveAccount').addEventListener('click', savePreferences); $('#savePersonalization').addEventListener('click', savePersonalization); $('#exportAll').addEventListener('click', exportAll); $('#deleteAll').addEventListener('click', deleteAll);
  $('#saveModel').addEventListener('click', async () => {
    const model = $('#ollamaModel').value.trim();
    if (!model) { toast('Inserisci il nome di un modello'); return; }
    try { await api('/api/settings/model', { method: 'POST', body: JSON.stringify({ model }) }); await refreshStatus(); toast(`Modello selezionato: ${model}`); }
    catch (error) { toast(error.message); }
  });
  $('#saveVisionModel').addEventListener('click', async () => {
    const model = $('#visionModel').value.trim(); if (!model) { toast('Inserisci il nome del modello visivo'); return; }
    try { await api('/api/settings/vision-model', { method: 'POST', body: JSON.stringify({ model }) }); await refreshStatus(); toast(`Modello visivo selezionato: ${model}`); }
    catch (error) { toast(error.message); }
  });
  $('#copyPullModel').addEventListener('click', () => copyText($('#pullModelCommand').textContent).then(() => toast('Comando copiato')));
  $('#copyPullVision').addEventListener('click', () => copyText($('#pullVisionCommand').textContent).then(() => toast('Comando copiato')));
  $('#voiceModeButton').addEventListener('click', openVoiceMode);
  $('#closeVoiceMode').addEventListener('click', closeVoiceMode);
  $('#voiceOrbButton').addEventListener('click', toggleVoiceInput);
  $('#voiceModeToggle').addEventListener('click', toggleVoiceInput);
  $('#voiceModeEnd').addEventListener('click', closeVoiceMode);
  $('#testVoice').addEventListener('click', () => { ensureAudioContext(); void speakText('Ciao, sono Avora. Questa è un’anteprima della voce selezionata. Posso leggere le risposte mentre le scrivo.'); });
  const commitVoice = () => {
    state.settings.voiceEngine = $('#voiceEngine').value === 'system' ? 'system' : 'natural';
    if (state.settings.voiceEngine === 'system') state.settings.systemVoiceName = $('#voiceSelect').value || ''; else state.settings.voiceName = $('#voiceSelect').value || 'it-IT-ElsaNeural';
    state.settings.voiceRate = $('#voiceRate').value || '1.05'; state.settings.autoReadResponses = $('#autoReadResponses').checked;
  };
  $('#saveVoicePreferences').addEventListener('click', () => { commitVoice(); persistPreferences(); toast('Impostazioni voce salvate'); });
  $('#voiceEngine').addEventListener('change', () => { state.settings.voiceEngine = $('#voiceEngine').value === 'system' ? 'system' : 'natural'; populateVoiceOptions(); persistPreferences(); });
  ['voiceSelect', 'voiceRate', 'autoReadResponses'].forEach(id => $(`#${id}`).addEventListener('change', () => { commitVoice(); persistPreferences(); }));
  // Neural voice options are provided by Avora, not browser-installed robotic voices.

  $$('.plan-choice').forEach(button => button.addEventListener('click', () => choosePlan(button.dataset.plan)));
  $('#changeAvatar').addEventListener('click', () => $('#avatarInput').click()); $('#avatarButton').addEventListener('click', () => $('#avatarInput').click());
  $('#avatarInput').addEventListener('change', event => { handleAvatar(event.target.files && event.target.files[0]); event.target.value = ''; });
  $('#removeAvatar').addEventListener('click', () => { delete state.settings.avatarData; persistPreferences(); updateProfile(); toast('Immagine rimossa'); });
  $$('[data-theme-choice]').forEach(button => button.addEventListener('click', () => { state.settings.theme = button.dataset.themeChoice; persistPreferences(); applyAppearance(); }));
  $$('[data-size-choice]').forEach(button => button.addEventListener('click', () => { state.settings.textSize = button.dataset.sizeChoice; persistPreferences(); applyAppearance(); }));
  if (window.matchMedia) { const query = matchMedia('(prefers-color-scheme: dark)'); const onChange = () => { if ((state.settings.theme || 'system') === 'system') applyAppearance(); }; if (query.addEventListener) query.addEventListener('change', onChange); }
  $$('.preset-card[data-preset]').forEach(card => $('[data-preset-action]', card).addEventListener('click', () => void usePreset(card.dataset.preset)));
  $('#installVision').addEventListener('click', () => { const name = (state.status && state.status.vision_model) || 'qwen3-vl:2b'; if (confirm(`Installare il modello visivo ${name}? Occupa circa 2 GB.`)) void startPull(name, 'vision'); });
  $('#hordeToggle').addEventListener('change', async event => {
    const on = event.target.checked;
    if (on && !confirm('La descrizione delle immagini verrà inviata in forma anonima alla rete AI Horde, gestita da volontari. Non inserire dati personali nelle richieste. Attivare?')) { event.target.checked = false; return; }
    try { await api('/api/settings/image-consent', { method: 'POST', body: JSON.stringify({ consent: on }) }); toast(on ? 'Generazione online gratuita attivata.' : 'Generazione online disattivata.'); await refreshGeneratedImages(); }
    catch (error) { event.target.checked = !on; toast(error.message); }
  });
  $('#autoModel').addEventListener('change', async event => {
    try { await api('/api/settings/auto', { method: 'POST', body: JSON.stringify({ auto: event.target.checked }) }); await refreshStatus(); toast(event.target.checked ? 'Selezione automatica del modello attiva.' : 'Selezione automatica disattivata.'); }
    catch (error) { event.target.checked = !event.target.checked; toast(error.message); }
  });
  $('#setupStart').addEventListener('click', () => void startAutoSetup());
  $('#setupDismiss').addEventListener('click', () => { state.settings.setupDismissed = true; persistPreferences(); renderSetupCard(); });
  $('#scrollDown').addEventListener('click', () => el.conversation.scrollTo({ top: el.conversation.scrollHeight, behavior: 'smooth' }));
  el.conversation.addEventListener('scroll', () => { $('#scrollDown').classList.toggle('hidden', nearBottom()); }, { passive: true });
  $('#personaSelect').addEventListener('change', event => changePersona(event.target.value));
  $('#compactChat').addEventListener('click', () => void compactCurrentChat());
  $('#previewClose').addEventListener('click', closePreview);
  $$('[data-preview-tab]').forEach(button => button.addEventListener('click', () => setPreviewTab(button.dataset.previewTab)));
  $('#previewCopy').addEventListener('click', () => { if (state.preview) copyText(state.preview.code).then(() => toast('Copiato')); });
  $('#previewDownload').addEventListener('click', () => { if (!state.preview) return; const [mime, ext] = PREVIEW_MIME[state.preview.lang] || ['text/plain', 'txt']; downloadFile(`avora-anteprima.${ext}`, state.preview.code, `${mime};charset=utf-8`); });
  $('#modelMenuButton').addEventListener('click', event => { event.stopPropagation(); toggleModelMenu(); });
  document.addEventListener('click', event => { if (!event.target.closest('#modelMenuWrap')) toggleModelMenu(false); });
  $('#collapseSidebar').addEventListener('click', () => setSidebarCollapsed(true));
  $('#expandSidebar').addEventListener('click', () => setSidebarCollapsed(false));
  document.addEventListener('keydown', event => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'b') { event.preventDefault(); setSidebarCollapsed(!document.querySelector('.app-shell').classList.contains('sidebar-collapsed')); } else if (event.key === 'Escape') toggleModelMenu(false); });
  $('#thinkToggle').addEventListener('click', () => setComposerMode('think', !state.think)); $('#researchToggle').addEventListener('click', () => setComposerMode('deepResearch', !state.deepResearch));
  $('#attachImage').addEventListener('click', () => $('#imageInput').click());
  $('#imageInput').addEventListener('change', async event => { const files = [...(event.target.files || [])]; event.target.value = ''; await addFiles(files); });
  $('#projectForm').addEventListener('submit', event => { event.preventDefault(); const name = $('#projectName').value.trim(); if (!name) return; const project = { id: (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`), name: name.slice(0, 50), instructions: $('#projectInstructions').value.trim().slice(0, 1000), created_at: new Date().toISOString() }; state.projects.unshift(project); localStorage.setItem('clara-projects', JSON.stringify(state.projects)); $('#projectName').value = ''; $('#projectInstructions').value = ''; renderProjects(); toast('Progetto creato'); });
  el.renameCurrent.addEventListener('click', async () => { const conversation = state.conversations.find(item => item.id === state.conversationId); if (conversation) await renameConversation(conversation); });
  el.exportCurrent.addEventListener('click', exportConversation);
  $$('[data-copy]').forEach(button => button.addEventListener('click', () => copyText(button.dataset.copy).then(() => toast('Comando copiato'))));
  el.form.addEventListener('submit', event => { event.preventDefault(); if (state.sending) { stopGeneration(); return; } void sendMessage(); });
  el.input.addEventListener('paste', event => { const files = [...((event.clipboardData && event.clipboardData.files) || [])]; if (files.length) { event.preventDefault(); void addFiles(files); } });
  (() => {
    const overlay = document.createElement('div'); overlay.className = 'drop-overlay hidden'; overlay.innerHTML = '<div><strong>Rilascia qui i file</strong><span>Foto, testo e codice</span></div>'; document.body.append(overlay);
    let depth = 0; const hasFiles = event => event.dataTransfer && [...(event.dataTransfer.types || [])].includes('Files');
    document.addEventListener('dragenter', event => { if (!hasFiles(event)) return; event.preventDefault(); depth += 1; overlay.classList.remove('hidden'); });
    document.addEventListener('dragover', event => { if (hasFiles(event)) event.preventDefault(); });
    document.addEventListener('dragleave', event => { if (!hasFiles(event)) return; depth = Math.max(0, depth - 1); if (!depth) overlay.classList.add('hidden'); });
    document.addEventListener('drop', event => { if (!hasFiles(event)) return; event.preventDefault(); depth = 0; overlay.classList.add('hidden'); if (!el.welcome.classList.contains('hidden') || !el.conversation.classList.contains('hidden')) void addFiles(event.dataTransfer.files); });
  })();
  el.input.addEventListener('input', () => { resizeInput(); updateCharCount(); updatePromptMenu(); });
  el.input.addEventListener('keydown', event => { if (onPromptKeys(event)) return; if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && state.settings.enterToSend) { event.preventDefault(); sendMessage(); } });
  $$('.suggestion-card').forEach(button => button.addEventListener('click', () => { el.input.value = button.dataset.prompt || ''; resizeInput(); updateCharCount(); el.input.focus(); }));
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); newChat(); }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'f') { event.preventDefault(); el.historySearchWrap.classList.remove('hidden'); el.historySearch.focus(); }
    if (event.key === 'Escape') { if (!$('#previewPanel').classList.contains('hidden')) { closePreview(); return; } if (state.sending) stopGeneration(); closeSettings(); closeSidebar(); closeFeatures(); if (!$('#voiceModeLayer').classList.contains('hidden')) closeVoiceMode(); }
  });

  // Keep diagnostics refreshed in Settings; the main chat UI stays uncluttered.
  window.setInterval(() => { if (!document.hidden) void refreshStatus(); }, 20000);

  (async function init() {
    loadPreferences(); renderPromptList(); if (window.matchMedia('(min-width: 681px)').matches) setSidebarCollapsed(Boolean(state.settings.sidebarCollapsed), false); { const hello = $('#welcomeHello'); if (hello) hello.textContent = greetingText(); } await Promise.all([refreshStatus(), refreshHistory(), loadPersonas()]); void pollPull(); renderSetupCard(); if (!obSeen()) showOnboarding();
    if (state.conversations.length) await loadConversation(state.conversations[0].id);
    updateCharCount();
  })();
})();
