// High-confidence email-domain typos. Keep this list aligned with the Backend
// validators so the browser only suggests corrections the server also knows.
const providers = new Set(['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'icloud.com']);
const tldTypos = new Map([
  ['con', 'com'], ['cmo', 'com'], ['comm', 'com'], ['coom', 'com'],
  ['vom', 'com'], ['cpm', 'com'], ['cim', 'com'], ['ocm', 'com'],
]);
const hostTypos = new Map([
  ['gmial', 'gmail.com'], ['gamil', 'gmail.com'], ['gnail', 'gmail.com'],
  ['gmaill', 'gmail.com'], ['gmal', 'gmail.com'], ['gmai', 'gmail.com'],
  ['gmali', 'gmail.com'], ['gmiall', 'gmail.com'],
  ['hotmial', 'hotmail.com'], ['hotmal', 'hotmail.com'], ['hotmai', 'hotmail.com'],
  ['hotmaill', 'hotmail.com'], ['homail', 'hotmail.com'], ['hotmil', 'hotmail.com'],
  ['outllok', 'outlook.com'], ['outlok', 'outlook.com'], ['outook', 'outlook.com'],
  ['outlookk', 'outlook.com'], ['outllook', 'outlook.com'], ['outllk', 'outlook.com'],
  ['yaho', 'yahoo.com'], ['yahooo', 'yahoo.com'], ['yhoo', 'yahoo.com'], ['yahho', 'yahoo.com'],
  ['iclod', 'icloud.com'], ['icoud', 'icloud.com'], ['iclou', 'icloud.com'],
  ['icloudd', 'icloud.com'], ['iclooud', 'icloud.com'], ['iclould', 'icloud.com'],
]);

export function suggestEmailCorrection(raw) {
  const email = (raw || '').trim().toLowerCase();
  if (email.split('@').length !== 2) return null;
  const at = email.lastIndexOf('@');
  const local = email.slice(0, at);
  const domain = email.slice(at + 1);
  if (!local || !domain || !domain.includes('.')) return null;
  if (providers.has(domain)) return null;
  const dot = domain.lastIndexOf('.');
  const host = domain.slice(0, dot);
  const tld = domain.slice(dot + 1);
  if (!host || !tld) return null;
  const correctedHost = hostTypos.get(host);
  const correctedTld = tldTypos.get(tld);
  if (correctedHost && tld === 'com') return `${local}@${correctedHost}`;
  if (!correctedHost && correctedTld && providers.has(`${host}.${correctedTld}`)) {
    return `${local}@${host}.${correctedTld}`;
  }
  if (correctedHost && correctedTld) return `${local}@${correctedHost}`;
  return null;
}
