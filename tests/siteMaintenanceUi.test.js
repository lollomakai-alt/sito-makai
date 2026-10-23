import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = path => readFile(new URL(path, import.meta.url), 'utf8');

test('site renders routes without a maintenance or startup loading gate', async () => {
  const app = await source('../src/app.jsx');
  assert.doesNotMatch(app, /site-maintenance|MaintenancePage|PageFallback|Caricamento…/);
  assert.match(app, /<Suspense fallback=\{null\}>/);
  assert.match(app, /<HeroSection \/>/);
  assert.match(app, /currentPath === "\/prenotazioni"/);
});
