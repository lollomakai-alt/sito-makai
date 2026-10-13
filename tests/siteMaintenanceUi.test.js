import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = path => readFile(new URL(path, import.meta.url), 'utf8');

test('maintenance page uses Makai branding and configured contacts', async () => {
  const page = await source('../src/pages/MaintenancePage.jsx');
  const contacts = await source('../src/data/contactInfo.js');
  const site = await source('../src/components/ContactsSection.jsx');
  assert.match(page, /La ciurma Makai è ai lavori!/);
  assert.match(page, /Le prenotazioni online sono temporaneamente sospese/);
  assert.match(page, /images\/logo\/Makai-grandline\.webp/);
  assert.match(page, /contactInfo\.whatsappHref/);
  assert.match(page, /contactInfo\.phoneHref/);
  assert.match(site, /contactInfo\.whatsappHref/);
  assert.match(contacts, /https:\/\/wa\.me\//);
});

test('site gate fails closed, refreshes and preserves privacy and existing booking management', async () => {
  const app = await source('../src/app.jsx');
  assert.match(app, /import \{[^}]*useEffect[^}]*\} from "react"/);
  assert.match(app, /fetch\("\/api\/site-maintenance", \{ cache: "no-store" \}\)/);
  assert.match(app, /if \(current\) setMaintenance\("active"\)/);
  assert.match(app, /setInterval\(refreshMaintenance, 30000\)/);
  assert.match(app, /currentPath !== "\/prenotazioni\/gestisci"/);
  assert.match(app, /currentPath !== "\/privacy"/);
});

test('mobile-first maintenance layout has touch contacts and desktop breakpoint', async () => {
  const css = await source('../src/styles/maintenance.css');
  assert.match(css, /min-height: 100svh/);
  assert.match(css, /min-height: 48px/);
  assert.match(css, /overflow-wrap: anywhere/);
  assert.match(css, /@media \(min-width: 768px\)/);
  assert.doesNotMatch(css, /overflow-x:\s*scroll/);
});
