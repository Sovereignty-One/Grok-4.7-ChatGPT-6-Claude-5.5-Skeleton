'use strict';

/**
 * KODER / SGHv119 server — authenticated control plane.
 *
 * Public GitHub remains public. This process may call configured external AI APIs.
 * Privileged HTTP and WebSocket operations require CONTROL_PLANE_TOKEN.
 * There is intentionally no anonymous/root-role fallback.
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cp = require('child_process');
const { URL } = require('url');

const PORT = Number.parseInt(process.env.PORT || '9898', 10);
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');
const PIPER_BIN = process.env.PIPER_BIN || 'piper';
const CONTROL_PLANE_TOKEN = process.env.CONTROL_PLANE_TOKEN || '';
const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || '';
const OPENAI_KEY = process.env.OPENAI_API_KEY || '';
const XAI_KEY = process.env.XAI_API_KEY || '';

if (CONTROL_PLANE_TOKEN.length < 32) {
  throw new Error('CONTROL_PLANE_TOKEN is required and must be at least 32 characters');
}

function tokenEqual(a, b) {
  const aa = Buffer.from(String(a || ''));
  const bb = Buffer.from(String(b || ''));
  return aa.length === bb.length && crypto.timingSafeEqual(aa, bb);
}

function bearer(req) {
  const match = /^Bearer\s+(.+)$/i.exec(req.headers.authorization || '');
  return match ? match[1] : '';
}

function authorized(req) {
  return tokenEqual(bearer(req), CONTROL_PLANE_TOKEN);
}

function ensureDataDir() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

function readJSON(name, fallback) {
  ensureDataDir();
  try { return JSON.parse(fs.readFileSync(path.join(DATA_DIR, name), 'utf8')); }
  catch (_) { return fallback; }
}

function writeJSON(name, value) {
  ensureDataDir();
  fs.writeFileSync(path.join(DATA_DIR, name), JSON.stringify(value, null, 2), { mode: 0o600 });
}

function respond(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': 'null',
    'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
  });
  res.end(payload);
}

function requireAuth(req, res) {
  if (authorized(req)) return true;
  respond(res, 401, { error: 'Unauthorized' });
  return false;
}

function readBody(req, limit = 1024 * 1024) {
  return new Promise((resolve, reject) => {
    let raw = '';
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size <= limit) raw += chunk;
      else reject(new Error('Request body too large'));
    });
    req.on('end', () => {
      if (size > limit) return;
      try { resolve(JSON.parse(raw || '{}')); }
      catch (_) { reject(new Error('Invalid JSON')); }
    });
    req.on('error', reject);
  });
}

function apiPost(url, headers, body) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const transport = parsed.protocol === 'https:' ? https : http;
    const payload = JSON.stringify(body);
    const req = transport.request({
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.pathname + parsed.search,
      method: 'POST',
      timeout: 30000,
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload), ...headers },
    }, res => {
      let raw = '';
      res.on('data', c => { raw += c; });
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch (_) { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('timeout', () => req.destroy(new Error('Upstream timeout')));
    req.on('error', reject);
    req.end(payload);
  });
}

async function callAI(model, system, messages, maxTokens) {
  const tokens = Math.min(Math.max(Number.parseInt(maxTokens || '4096', 10) || 4096, 1), 131072);
  if (model === 'claude') {
    if (!ANTHROPIC_KEY) return { error: 'ANTHROPIC_API_KEY not configured' };
    const r = await apiPost('https://api.anthropic.com/v1/messages',
      { 'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01' },
      { model: 'claude-opus-4-7', max_tokens: tokens, system, messages });
    return r.body?.content?.[0]?.text ? { text: r.body.content[0].text } : { error: r.body?.error?.message || 'Claude API error', status: r.status };
  }
  if (model === 'gpt') {
    if (!OPENAI_KEY) return { error: 'OPENAI_API_KEY not configured' };
    const r = await apiPost('https://api.openai.com/v1/chat/completions',
      { Authorization: `Bearer ${OPENAI_KEY}` },
      { model: 'gpt-5.4-mini', max_tokens: tokens, messages: [{ role: 'system', content: system }, ...messages] });
    return r.body?.choices?.[0]?.message?.content ? { text: r.body.choices[0].message.content } : { error: r.body?.error?.message || 'OpenAI API error', status: r.status };
  }
  if (model === 'grok') {
    if (!XAI_KEY) return { error: 'XAI_API_KEY not configured' };
    const r = await apiPost('https://api.x.ai/v1/chat/completions',
      { Authorization: `Bearer ${XAI_KEY}` },
      { model: 'grok-4.3', max_tokens: tokens, messages: [{ role: 'system', content: system }, ...messages] });
    return r.body?.choices?.[0]?.message?.content ? { text: r.body.choices[0].message.content } : { error: r.body?.error?.message || 'xAI API error', status: r.status };
  }
  return { error: 'Unknown model' };
}

const COMMANDS = new Map([
  ['pwd', ['pwd']], ['ls', ['ls']], ['date', ['date']], ['whoami', ['whoami']],
  ['hostname', ['hostname']], ['uname', ['uname']], ['node --version', ['node', '--version']],
  ['npm --version', ['npm', '--version']], ['python3 --version', ['python3', '--version']],
  ['python --version', ['python', '--version']],
]);
const SAFE_BASE = new Set(['echo', 'cat', 'head', 'tail', 'wc', 'ls']);
const SHELL_META = /[;&|`$<>()\\\n\r]/;

function executeCommand(command) {
  const value = String(command || '').trim();
  if (COMMANDS.has(value)) {
    const [bin, ...args] = COMMANDS.get(value);
    try { return { output: cp.execFileSync(bin, args, { timeout: 5000, encoding: 'utf8' }), exit: 0 }; }
    catch (e) { return { output: e.message, exit: e.status || 1 }; }
  }
  const tokens = value ? value.split(/\s+/) : [];
  if (tokens.length && SAFE_BASE.has(tokens[0]) && tokens.every(t => !SHELL_META.test(t))) {
    try { return { output: cp.execFileSync(tokens[0], tokens.slice(1), { timeout: 5000, encoding: 'utf8' }), exit: 0 }; }
    catch (e) { return { output: e.message, exit: e.status || 1 }; }
  }
  return { output: 'Command denied by execution allowlist', exit: 1 };
}

async function handle(req, res) {
  if (req.method === 'OPTIONS') return respond(res, 204, {});
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

  if (req.method === 'GET' && url.pathname === '/health') {
    return respond(res, 200, { status: 'healthy', service: 'server_9898', control_plane: 'authenticated', timestamp: new Date().toISOString() });
  }
  if (!requireAuth(req, res)) return;

  try {
    if (req.method === 'POST' && url.pathname === '/api/ai/chat') {
      const body = await readBody(req);
      const messages = Array.isArray(body.messages) && body.messages.length ? body.messages : [{ role: 'user', content: String(body.text || '') }];
      const result = await callAI(body.model || 'claude', String(body.system || ''), messages, body.max_tokens);
      return respond(res, result.error ? 502 : 200, result);
    }
    if (req.method === 'POST' && url.pathname === '/api/execute-command') {
      const body = await readBody(req);
      return respond(res, 200, executeCommand(body.command));
    }
    if (req.method === 'GET' && url.pathname === '/api/memory') return respond(res, 200, readJSON('memory.json', []));
    if (req.method === 'POST' && url.pathname === '/api/memory') {
      const body = await readBody(req);
      const items = readJSON('memory.json', []);
      const entry = { id: crypto.randomUUID(), title: String(body.title || 'Note').slice(0, 200), content: String(body.content || '').slice(0, 2000), ts: new Date().toISOString(), auto: Boolean(body.auto) };
      items.push(entry); writeJSON('memory.json', items.slice(-200)); return respond(res, 201, entry);
    }
    if (req.method === 'DELETE' && url.pathname.startsWith('/api/memory/')) {
      const id = url.pathname.slice('/api/memory/'.length); const items = readJSON('memory.json', []); const next = items.filter(e => e.id !== id);
      writeJSON('memory.json', next); return respond(res, 200, { deleted: items.length - next.length });
    }
    if (req.method === 'GET' && url.pathname === '/api/audit') return respond(res, 200, readJSON('audit.json', []));
    if (req.method === 'POST' && url.pathname === '/api/audit') {
      const body = await readBody(req); const entries = readJSON('audit.json', []);
      const entry = { id: crypto.randomUUID(), action: String(body.action || 'EVENT').slice(0, 100), detail: String(body.detail || '').slice(0, 500), ts: new Date().toISOString() };
      entries.push(entry); writeJSON('audit.json', entries.slice(-1000)); return respond(res, 201, entry);
    }
    const dashboard = path.join(__dirname, 'SGHv119.html');
    if (req.method === 'GET' && url.pathname === '/') {
      if (!fs.existsSync(dashboard)) return respond(res, 404, { error: 'Dashboard not found' });
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
      return res.end(fs.readFileSync(dashboard));
    }
    return respond(res, 404, { error: 'Not found' });
  } catch (e) {
    return respond(res, 400, { error: e.message });
  }
}

const createServer = process.env.TLS_CERT && process.env.TLS_KEY
  ? https.createServer({ cert: fs.readFileSync(process.env.TLS_CERT), key: fs.readFileSync(process.env.TLS_KEY) }, handle)
  : http.createServer(handle);

let wss;
try {
  const { WebSocketServer } = require('ws');
  wss = new WebSocketServer({ server: createServer });
  wss.on('connection', (ws, req) => {
    if (!tokenEqual(bearer(req), CONTROL_PLANE_TOKEN)) return ws.close(1008, 'Unauthorized');
    ws.on('message', async raw => {
      let msg; try { msg = JSON.parse(raw); } catch (_) { return ws.send(JSON.stringify({ type: 'error', error: 'Invalid JSON' })); }
      if (msg.type === 'ping') return ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
      if (msg.type === 'ai_query') {
        const result = await callAI(msg.model || 'claude', String(msg.system || ''), [{ role: 'user', content: String(msg.text || '') }]);
        return ws.send(JSON.stringify({ type: 'ai_response', model: msg.model || 'claude', text: result.text || '', error: result.error || null }));
      }
      if (msg.type === 'piper_speak') {
        const clean = String(msg.text || '').replace(/[<>]/g, '').slice(0, 500);
        const proc = cp.spawn(PIPER_BIN, ['--output-raw'], { stdio: ['pipe', 'pipe', 'ignore'] });
        const chunks = []; proc.stdout.on('data', c => chunks.push(c)); proc.stdout.on('end', () => ws.send(JSON.stringify({ type: 'audio', data: Buffer.concat(chunks).toString('base64') })));
        proc.on('error', () => ws.send(JSON.stringify({ type: 'error', error: 'Piper unavailable' })));
        proc.stdin.end(clean);
      }
    });
  });
} catch (e) {
  console.error('[server_9898] WebSocket disabled:', e.message);
}

createServer.listen(PORT, '0.0.0.0', () => console.log(`[server_9898] listening on ${PORT}; control plane authenticated`));
