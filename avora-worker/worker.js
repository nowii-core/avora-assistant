// avora-worker/worker.js
// Proxy sicuro per Groq API — la chiave vive solo qui come secret.
// Deploy: wrangler deploy
// Secret: wrangler secret put GROQ_API_KEY

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const DEFAULT_MODEL = 'llama-3.1-8b-instant';

// Imposta qui il tuo dominio GitHub Pages per limitare l’accesso.
// Esempio: 'https://tuonome.github.io'
// Lascia '*' solo per test, poi restringi.
const ALLOWED_ORIGIN = '*';

function corsHeaders(origin = ALLOWED_ORIGIN) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Avora-Client',
    'Access-Control-Max-Age': '86400'
  };
}

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';

    // Preflight CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405, headers: corsHeaders(origin) });
    }

    // Opzionale: header condiviso per scoraggiare bot.
    // Se lo attivi, aggiungi lo stesso valore in app.js (WORKER_CLIENT_HEADER).
    // const client = request.headers.get('X-Avora-Client');
    // if (client !== env.AVORA_CLIENT_SECRET) {
    //   return new Response('Forbidden', { status: 403, headers: corsHeaders(origin) });
    // }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ error: 'JSON non valido' }), {
        status: 400,
        headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' }
      });
    }

    // Il frontend può inviare { model?, messages, stream?, temperature? }
    const payload = {
      model: body.model || DEFAULT_MODEL,
      messages: body.messages || [],
      stream: body.stream !== false, // default: streaming
      temperature: typeof body.temperature === 'number' ? body.temperature : 0.7
    };

    if (!payload.messages.length) {
      return new Response(JSON.stringify({ error: 'messages mancante' }), {
        status: 400,
        headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' }
      });
    }

    const upstream = await fetch(GROQ_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.GROQ_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    // Pass-through dello streaming: non consumiamo il body.
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.set('Access-Control-Allow-Origin', origin || ALLOWED_ORIGIN);
    responseHeaders.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
    responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, X-Avora-Client');

    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders
    });
  }
};