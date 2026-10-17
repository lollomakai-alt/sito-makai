import { isIP } from 'node:net';

const routes = {
  GET: /^\/api\/(?:health|site-maintenance|booking-settings|booking-availability|menu)$/,
  POST: /^\/api\/(?:bookings|chat|booking-management\/(?:view|reconfirm|request))$/,
};
const siteHosts = new Set(['www.makaipigneto.it', 'makaipigneto.it', 'sito-makai.vercel.app']);

export default async function handler(request, response) {
  response.setHeader('Cache-Control', 'no-store');
  const incoming = new URL(request.url, 'https://site.invalid');
  if (incoming.pathname === '/api/backend-gateway') {
    const route = request.query?.__backend_route ?? incoming.searchParams.get('__backend_route');
    if (typeof route !== 'string' || !/^[a-z0-9/-]+$/.test(route)) {
      return response.status(404).json({ detail: 'Percorso non disponibile.' });
    }
    incoming.pathname = '/api/' + route;
  }
  incoming.searchParams.delete('__backend_route');
  if (!routes[request.method]?.test(incoming.pathname)) {
    return response.status(404).json({ detail: 'Percorso non disponibile.' });
  }
  const target = process.env.API_PROXY_TARGET;
  const secret = process.env.MAKAI_SITE_PROXY_SECRET;
  let base;
  try {
    base = new URL(target);
    if (base.protocol !== 'https:' || base.username || base.password || base.pathname !== '/' || base.search || base.hash
        || siteHosts.has(base.hostname) || base.host === request.headers.host
        || typeof secret !== 'string' || secret.length < 32) throw new Error();
  } catch {
    return response.status(503).json({ detail: 'Collegamento al Backend Makai non configurato.' });
  }
  const headers = { 'x-makai-site-proxy-key': secret };
  for (const name of ['content-type', 'accept', 'origin']) {
    if (typeof request.headers[name] === 'string') headers[name] = request.headers[name];
  }
  const ip = request.headers['x-vercel-forwarded-for'] ?? request.headers['x-forwarded-for'] ?? request.socket?.remoteAddress;
  if (typeof ip === 'string' && isIP(ip.split(',')[0].trim())) headers['x-makai-client-ip'] = ip.split(',')[0].trim();
  const options = { method: request.method, headers, redirect: 'error', signal: AbortSignal.timeout(115000) };
  if (request.method === 'POST' && request.body !== undefined && request.body !== null) {
    options.body = typeof request.body === 'string' || Buffer.isBuffer(request.body) ? request.body : JSON.stringify(request.body);
  }
  try {
    const upstream = await fetch(new URL(incoming.pathname + incoming.search, base), options);
    for (const name of ['content-type', 'retry-after']) {
      const value = upstream.headers.get(name);
      if (value) response.setHeader(name, value);
    }
    return response.status(upstream.status).send(Buffer.from(await upstream.arrayBuffer()));
  } catch {
    return response.status(502).json({ detail: 'Backend Makai momentaneamente non raggiungibile.' });
  }
}
