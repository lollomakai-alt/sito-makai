import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('service and time pickers use live service slots and clear dependent selections on change', async () => {
  const page = await readFile(new URL('../src/pages/BookingPage.jsx', import.meta.url), 'utf8');
  assert.match(page, /<fieldset className="booking-choice-group">/);
  assert.match(page, /name="booking-service"/);
  assert.match(page, /checked=\{bookingType === service\.value\}/);
  assert.match(page, /setBookingTime\(''\); setConfirmedGuests\(null\); setSelected\(null\); setReviewed\(false\)/);
  assert.match(page, /settings\?\.services\?\.\[bookingType\]/);
  assert.match(page, /name="time" required value=\{shift\.value\} checked=\{bookingTime === shift\.value\}/);
  assert.doesNotMatch(page, /Tre turni: cena/);
  assert.match(page, /online_closed: t\("Prenotazioni online chiuse"/);
  assert.doesNotMatch(page, /<select[^>]*(?:booking-service|name="time")/);
});

test('service and time controls retain keyboard focus, disabled styling, touch size and narrow responsive grids', async () => {
  const css = await readFile(new URL('../src/styles/prenotazioni.css', import.meta.url), 'utf8');
  assert.match(css, /:focus-visible \+ \.booking-choice-face/);
  assert.match(css, /:disabled \+ \.booking-choice-face/);
  assert.match(css, /\.booking-time-face \{ min-height: 56px/);
  assert.match(css, /\.booking-day\.closed \{/);
  assert.match(css, /\.booking-day\.online_closed, \.booking-day\.full/);
  assert.match(css, /grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(css, /grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/);
  assert.doesNotMatch(css, /booking-(?:service|time)-options[^\n]*overflow-x/);
});
