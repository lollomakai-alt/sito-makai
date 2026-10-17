import test from 'node:test';
import assert from 'node:assert/strict';
import { receiptMessage, managementMessage, formError, explainInvalidInput, clearInputExplanation } from '../src/i18n/bookingFeedback.js';

const details = { guests: 4, time: '00:00', date: 'sabato 17 ottobre 2026' };

test('receipt distinguishes confirmation, pending review, acceptance, rejection and cancelled replay', () => {
  const confirmed = receiptMessage({ status: 'confirmed' }, details);
  assert.match(confirmed, /prenotazione confermata/);
  assert.match(confirmed, /sabato 17 ottobre 2026 per 4 persone alle 00:00/);
  assert.match(receiptMessage({ status: 'pending' }, details), /non è ancora confermata/);
  assert.match(receiptMessage({ status: 'accepted' }, details), /non indica un tavolo assegnato/);
  assert.match(receiptMessage({ status: 'rejected' }, details), /non ha potuto accettare/);
  assert.match(receiptMessage({ status: 'cancelled' }, details), /risulta cancellata/);
  for (const status of ['accepted', 'rejected']) {
    assert.doesNotMatch(receiptMessage({ status }, details), /[Rr]iceverai|ti risponderà/);
  }
});

test('unknown receipt and management outcomes never fabricate success or pending requests', () => {
  assert.match(receiptMessage({ status: 'unexpected' }, details), /non può confermare l’esito/);
  assert.match(managementMessage('unexpected'), /non può confermare l’esito/);
  assert.doesNotMatch(managementMessage('unexpected'), /Richiesta ricevuta/);
  assert.match(managementMessage('pending'), /modifica non è ancora confermata/);
  assert.match(managementMessage('cancelled'), /Se era assegnato un tavolo/);
  assert.match(managementMessage('applied'), /modifica alla prenotazione è confermata/);
  assert.match(managementMessage('unchanged'), /Nessuna modifica necessaria/);
});

test('English receipt keeps pending and assigned-table distinctions', () => {
  const en = { ...details, language: 'en' };
  assert.match(receiptMessage({ status: 'pending' }, en), /not confirmed yet/);
  assert.match(receiptMessage({ status: 'accepted' }, en), /does not indicate an assigned table/);
  assert.match(receiptMessage({ status: 'unknown' }, en), /cannot confirm the outcome/);
});

test('errors preserve server guidance and hide native transport/parsing messages without claiming failure', () => {
  assert.match(formError(new Error('Collegamento non valido o scaduto.')), /Collegamento non valido o scaduto/);
  for (const error of [new TypeError('Failed to fetch'), new SyntaxError('Unexpected token'), { name: 'TimeoutError' }]) {
    const message = formError(error);
    assert.match(message, /esito dell’operazione non è verificato/);
    assert.doesNotMatch(message, /Failed to fetch|Unexpected token/);
  }
});

test('input explanations keep privacy mandatory, marketing optional, and clear on correction', () => {
  let explanation = '';
  const target = { name: 'privacy', validity: { valid: false, valueMissing: true }, setCustomValidity(value) { explanation = value; } };
  explainInvalidInput({ target });
  assert.match(explanation, /privacy/);
  assert.match(explanation, /marketing resta facoltativo/);
  clearInputExplanation({ target });
  assert.equal(explanation, '');
  target.validity = { valid: false, typeMismatch: true }; target.type = 'email';
  explainInvalidInput({ target }, 'en');
  assert.match(explanation, /valid address/);
  target.validity = { valid: true };
  explainInvalidInput({ target });
  assert.equal(explanation, '');
});
