import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

// Exercise the actual hook with browser/GSAP boundaries mocked, no real browser.
const source = readFileSync(new URL('../src/hooks/usePageMotion.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '')
  .replace('export function sectionScrollTop', 'function sectionScrollTop')
  .replace('export default function usePageMotion', 'function usePageMotion')
  .replaceAll('import.meta.env.BASE_URL', '"/"');

function setup({ hash = '', reduced = false } = {}) {
  const handlers = new Map();
  const frames = new Map();
  const stats = { updates: 0, refreshes: 0, animations: 0, completedScrubs: 0 };
  let serial = 0;
  let cleanup;
  const style = new Map();
  const nav = { getBoundingClientRect: () => ({ height: 100 }) };
  const window = {
    scrollY: 0,
    location: new URL(`http://localhost:5173/${hash}`),
    scrollTo({ top, behavior }) {
      assert.ok(stats.refreshes > 0, 'measure layout before calculating the destination');
      assert.equal(behavior, 'instant');
      this.scrollY = top;
    },
    history: { pushState(_, __, url) { window.location = new URL(url); } },
    addEventListener(name, fn) { handlers.set(name, fn); },
    removeEventListener(name, fn) { if (handlers.get(name) === fn) handlers.delete(name); },
  };
  const target = { id: 'chi-siamo', getBoundingClientRect: () => ({ top: 600 - window.scrollY }) };
  const element = { matches: () => true };
  const root = {
    style: { getPropertyValue: k => style.get(k) || '', setProperty: (k, v) => style.set(k, v), removeProperty: k => style.delete(k) },
    querySelector: () => nav,
    querySelectorAll: () => [{ children: [element] }],
    contains: t => t === target,
    addEventListener: (name, fn) => handlers.set(`root:${name}`, fn),
    removeEventListener: name => handlers.delete(`root:${name}`),
  };
  const gsap = {
    registerPlugin() {}, set() {}, utils: { toArray: () => [] },
    context(fn) { fn(); return { revert() {} }; },
    matchMedia() { let release; return { add(_, fn) { if (!reduced) release = fn(); }, revert() { release?.(); } }; },
    fromTo(_, __, options) {
      stats.animations++;
      return {
        progress() { assert.fail('Do not force reveal progress: preserve the scrub animation'); },
        scrollTrigger: options.scrollTrigger ? { progress: 0.8, getTween: () => ({ progress() { stats.completedScrubs++; } }) } : undefined,
      };
    },
  };
  const context = vm.createContext({
    root, window, document: { getElementById: id => id === target.id ? target : null }, URL,
    gsap, ScrollTrigger: { refresh() { stats.refreshes++; }, update() { stats.updates++; }, maxScroll: () => 2000 },
    useLayoutEffect(fn) { cleanup = fn(); },
    ResizeObserver: class { observe() {} disconnect() {} },
    requestAnimationFrame(fn) { frames.set(++serial, fn); return serial; },
    cancelAnimationFrame(id) { frames.delete(id); },
  });
  vm.runInContext(`${source}\nusePageMotion({current: root}, '/');`, context);
  return { handlers, window, stats, target, cleanup, frames, flush() {
    for (let i = 0; frames.size && i < 10; i++) {
      const batch = [...frames.values()]; frames.clear(); batch.forEach(fn => fn());
    }
  } };
}

test('direct fragment entry aligns below navbar and syncs without a scroll event', () => {
  const h = setup({ hash: '#chi-siamo' });
  h.flush();
  assert.equal(h.window.scrollY, 500);
  assert.ok(h.stats.updates > 0);
  assert.equal(h.stats.completedScrubs, 0, 'anchor navigation must not skip scrub movement');
  h.cleanup();
});

test('nav click updates the URL, scrolls immediately and refreshes', () => {
  const h = setup();
  let prevented = false;
  const anchor = { href: 'http://localhost:5173/#chi-siamo', target: '', hasAttribute: () => false };
  h.handlers.get('root:click')({ button: 0, target: { closest: () => anchor }, preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(h.window.location.hash, '#chi-siamo');
  assert.equal(h.window.scrollY, 500);
  h.flush(); h.cleanup();
});

test('manual scroll is not undone by late image loads', () => {
  const h = setup({ hash: '#chi-siamo' });
  h.flush();
  h.handlers.get('wheel')({ type: 'wheel' });
  h.window.scrollY = 900;
  h.handlers.get('root:load')();
  h.flush();
  assert.equal(h.window.scrollY, 900);
  h.cleanup();
});

test('reduced motion keeps content unhidden and preserves anchor offset', () => {
  const h = setup({ hash: '#chi-siamo', reduced: true });
  h.flush();
  assert.equal(h.stats.animations, 0);
  assert.equal(h.window.scrollY, 500);
  h.cleanup();
});

test('history and BFCache navigation realign and update animations', () => {
  const h = setup();
  for (const event of ['hashchange', 'popstate', 'pageshow']) {
    h.window.location.hash = '#chi-siamo';
    h.window.scrollY = 0;
    h.handlers.get(event)();
    h.flush();
    assert.equal(h.window.scrollY, 500);
  }
  h.cleanup();
});

test('StrictMode cleanup cancels all pending frames and event handlers', () => {
  const h = setup({ hash: '#chi-siamo' });
  h.cleanup();
  assert.equal(h.frames.size, 0);
  assert.equal(h.handlers.size, 0);
  const next = setup({ hash: '#chi-siamo' });
  next.flush();
  assert.equal(next.window.scrollY, 500);
  next.cleanup();
});
