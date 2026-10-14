import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('booking form keeps required privacy separate from optional unchecked marketing for both services', async () => {
  const page = await readFile(new URL('../src/pages/BookingPage.jsx', import.meta.url), 'utf8');
  assert.match(page, /type="checkbox" required name="privacy"/);
  assert.match(page, /type="checkbox" name="marketing"/);
  assert.doesNotMatch(page, /name="marketing"[^>]*checked/);
  assert.match(page, /<section className="booking-offers" aria-labelledby="booking-offers-title">/);
  assert.doesNotMatch(page, /bookingType === "normale" \? <section className="booking-offers"/);
});
