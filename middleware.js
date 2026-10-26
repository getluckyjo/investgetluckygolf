/* Site-wide password gate (Vercel Routing Middleware).

   Every path is gated except the unlock form's POST target and the fonts and
   logos the gate page itself shows. The password lives only in the Vercel
   project's SITE_PASSWORD environment variable — never in this repository.
   If SITE_PASSWORD is not set, the site stays shut: no fallback password.

   The cookie holds a salted SHA-256 of the password, never the password, so
   changing SITE_PASSWORD signs everyone out. */

let passThrough; // undefined = not yet tried, null = unavailable
async function cont() {
  if (passThrough === undefined) {
    try {
      ({ next: passThrough } = await import('@vercel/functions'));
    } catch {
      passThrough = null;
    }
  }
  return passThrough ? passThrough() : undefined;
}

const COOKIE = 'gl_invest';
const SALT = 'get-lucky-invest-2027:';
const MAX_AGE = 60 * 60 * 24 * 30; // 30 days
const OPEN = (p) => p.startsWith('/_vercel/') || p.startsWith('/assets/fonts/') || p.startsWith('/assets/logos/');

async function sha256(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function readCookie(header, name) {
  for (const part of (header || '').split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === name) return v.join('=');
  }
  return null;
}

/** Compare without stopping at the first difference. */
function same(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export default async function middleware(request) {
  const url = new URL(request.url);
  if (OPEN(url.pathname)) return await cont();

  const pw = process.env.SITE_PASSWORD;
  if (!pw) return page('/', 'closed');
  const token = await sha256(SALT + pw);

  if (same(readCookie(request.headers.get('cookie'), COOKIE), token)) {
    if (url.pathname === '/__unlock') return new Response(null, { status: 303, headers: { Location: '/' } });
    return await cont();
  }

  if (url.pathname === '/__unlock' && request.method === 'POST') {
    let supplied = '';
    let dest = '/';
    try {
      const form = await request.formData();
      supplied = String(form.get('password') || '');
      const raw = String(form.get('next') || '/');
      dest = raw.startsWith('/') && !raw.startsWith('//') ? raw : '/';
    } catch { /* treat as a wrong password */ }
    if (same(await sha256(SALT + supplied), token)) {
      return new Response(null, {
        status: 303,
        headers: {
          Location: dest,
          'Set-Cookie': `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${MAX_AGE}`,
        },
      });
    }
    return page(dest, 'retry');
  }

  return page(url.pathname + url.search, 'ask');
}

function page(dest, state) {
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const form = state === 'closed'
    ? '<p class="err">This site is not open yet.</p>'
    : `${state === 'retry' ? '<p class="err">That password is not right. Try again.</p>' : ''}
    <form method="POST" action="/__unlock">
      <input type="hidden" name="next" value="${esc(dest)}">
      <label for="pw" class="sr">Password</label>
      <input id="pw" name="password" type="password" placeholder="Password" autocomplete="current-password" autofocus required>
      <button type="submit">Enter</button>
    </form>`;
  return new Response(`<!DOCTYPE html>
<html lang="en-ZA"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Get Lucky Golf — investor briefing</title>
<style>
  @font-face { font-family: "Poster Gothic"; src: url("/assets/fonts/PosterGothicRoundATF-Heavy.woff2") format("woff2"); font-weight: 800; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px; background: #0c160e;
         background-image: radial-gradient(rgba(214,251,75,.09) 1px, transparent 1.2px); background-size: 22px 22px;
         color: #f5eede; font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  main { width: 100%; max-width: 25rem; text-align: center; }
  img { height: 64px; width: auto; margin: 0 auto 18px; display: block; }
  h1 { font-family: "Poster Gothic", "Arial Black", sans-serif; font-weight: 800; text-transform: uppercase; font-size: 2.2rem; line-height: .95; margin: 0 0 10px; }
  h1 span { color: #d6fb4b; }
  p { margin: 0 0 22px; color: rgba(245,238,222,.75); font-size: .95rem; line-height: 1.55; }
  form { display: grid; gap: 10px; }
  input { width: 100%; height: 50px; padding: 0 18px; font-size: 1rem; border-radius: 999px; border: 1px solid rgba(245,238,222,.25);
          background: rgba(245,238,222,.06); color: #f5eede; }
  input::placeholder { color: rgba(245,238,222,.45); }
  input:focus-visible { outline: 3px solid #d6fb4b; outline-offset: 2px; }
  button { height: 50px; border: 0; border-radius: 999px; background: #d6fb4b; color: #345231; font-weight: 700; font-size: 1rem; cursor: pointer; }
  button:hover { background: #c5ec35; }
  .err { color: #ffd9d0; }
  .sr { position: absolute; left: -9999px; }
  .foot { margin: 26px 0 0; font-size: .78rem; color: rgba(245,238,222,.5); }
</style></head>
<body>
  <main>
    <img src="/assets/logos/logo-corner.svg" alt="Get Lucky">
    <h1>Investor <span>briefing</span></h1>
    <p>This material is private. Enter the password you were given.</p>
    ${form}
    <p class="foot">Get Lucky Golf Club (Pty) Ltd · confidential</p>
  </main>
</body></html>`, {
    status: state === 'closed' ? 503 : 401,
    headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex, nofollow' },
  });
}
