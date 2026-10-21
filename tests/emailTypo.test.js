import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { suggestEmailCorrection } from '../src/utils/emailTypo.js';

test('single and combined common typos produce a suggestion without rewriting the value', () => {
  const cases = {
    'mario@gnail.com': 'mario@gmail.com',
    'mario@gmial.com': 'mario@gmail.com',
    'mario@gamil.com': 'mario@gmail.com',
    'mario@gmal.com': 'mario@gmail.com',
    'mario@gmai.com': 'mario@gmail.com',
    'mario@gmail.con': 'mario@gmail.com',
    'mario@gnail.con': 'mario@gmail.com',
    'mario@gmial.con': 'mario@gmail.com',
    'mario@hotmial.con': 'mario@hotmail.com',
    'mario@outllok.con': 'mario@outlook.com',
    'mario@yaho.con': 'mario@yahoo.com',
    'mario@iclod.con': 'mario@icloud.com',
    'Mario.Rossi@GNAIL.CON': 'mario.rossi@gmail.com',
  };
  for (const [value, expected] of Object.entries(cases)) {
    assert.equal(suggestEmailCorrection(value), expected, value);
  }
  const raw = 'Mario@gnail.con';
  suggestEmailCorrection(raw);
  assert.equal(raw, 'Mario@gnail.con');
});

test('valid and unusual domains are not blocked only because they are uncommon', () => {
  for (const value of [
    'mario@gmail.com', 'mario@hotmail.com', 'mario@outlook.com',
    'mario@yahoo.com', 'mario@icloud.com', 'mario@mail.com',
    'mario@ymail.com', 'mario@gmx.com', 'mario@protonmail.com',
    'mario@googlemail.com', 'mario@studio.legalmail.it',
    'mario@azienda.example', 'mario@gmail.co.uk', 'mario@icloud.co.uk',
    'mario@gmall.com', 'mario@gnail.example', 'mario@gnail.com.br',
    'mario@notgmail.com',
  ]) {
    assert.equal(suggestEmailCorrection(value), null, value);
  }
});

test('booking form shows the suggestion by the email field and applies it only on explicit confirmation', async () => {
  const page = await readFile(new URL('../src/pages/BookingPage.jsx', import.meta.url), 'utf8');
  assert.match(page, /import \{ suggestEmailCorrection \} from "\.\.\/utils\/emailTypo"/);
  assert.match(page, /onChange=\{handleEmailChange\}/);
  assert.match(page, /setEmailSuggestion\(suggestEmailCorrection\(value\)\)/);
  assert.match(page, /id="booking-email-suggestion"/);
  assert.match(page, /className="booking-email-suggestion"/);
  assert.match(page, /role="status" aria-live="polite"/);
  assert.match(page, /onClick=\{applyEmailSuggestion\}/);
  assert.match(page, /setEmailValue\(emailSuggestion\)/);
  const changeHandler = page.match(/function handleEmailChange\(event\) \{[\s\S]*?\n  \}/)?.[0] || '';
  assert.match(changeHandler, /setEmailValue\(value\)/);
  assert.doesNotMatch(changeHandler, /setEmailValue\(emailSuggestion\)/);
});
