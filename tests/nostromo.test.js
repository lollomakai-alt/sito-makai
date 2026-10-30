import test from 'node:test';
import assert from 'node:assert/strict';
import { localReply, requestReply, errorMessage, quickQuestionGroups, quickQuestions } from '../src/utils/nostromo.js';

const ok = data => new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });
const noNetwork = () => { assert.fail('This request must not reach the conversational API'); };
const menu = {
  cocktails: [{ name_it: 'Drink test A', description_it: 'Rum e cocco', price: 10.5 }, { name_it: 'Drink test B', description_it: 'Rum e cacao', price: '11' }, { name_it: 'Drink test C', description_it: 'Rum', price: null }, { name_it: 'Drink test D', description_it: 'Rum', price: 12 }],
  analcolici: [{ name_it: 'Bevanda test', description_it: 'Succo di mela', price: 6 }],
  secondi_main: [{ name_it: 'Piatto test', description_it: 'Pesce', price: 15 }],
  snack: [], sushi: [], primi_starters: [], dolci: [], volcanoes: [],
};
const menuFetch = async (url, options) => {
  assert.equal(url, '/api/menu');
  assert.equal(options.method, 'GET');
  assert.equal(options.cache, 'no-store');
  assert.equal(options.body, undefined);
  return ok({ menu });
};

test('greetings, thanks and unclear questions receive useful local guidance', async () => {
  assert.equal(quickQuestions.length, 4);
  assert.deepEqual(quickQuestionGroups.map(group => group.id), ['food', 'drink', 'locale', 'events']);
  assert.ok(quickQuestionGroups[2].questions.some(question => /parcheggi/i.test(question)));
  assert.ok(quickQuestionGroups[3].questions.some(question => /compleanno|eventi/i.test(question)));
  for (const message of ['Ciao!', 'Ahoy', 'buonasera', 'Hi']) {
    assert.match((await requestReply(message, { fetchImpl: noNetwork })).reply, /Sono Nostromo/);
  }
  assert.match((await requestReply('Grazie mille!', { fetchImpl: noNetwork })).reply, /Ai tuoi ordini/);
  for (const message of ['aiuto', 'non ho capito', 'cosa mi consigli?']) {
    const result = await requestReply(message, { fetchImpl: noNetwork });
    assert.match(result.reply, /dettaglio in più/);
    assert.equal(result.quickReplies.length, 4);
  }
  const choice = await requestReply('Mostrami il menù', { fetchImpl: noNetwork });
  assert.match(choice.reply, /da mangiare o da bere/);
});

test('the rotating quick-question catalog covers four customer topics with seven choices each', () => {
  assert.equal(quickQuestionGroups.length, 4);
  assert.deepEqual(quickQuestionGroups.map(group => group.questions.length), [7, 7, 7, 7]);
  assert.match(quickQuestionGroups[0].questions[6], /allergia/);
  assert.match(quickQuestionGroups[1].questions[4], /analcolici/);
  assert.match(quickQuestionGroups[2].questions[0], /parcheggi/);
  assert.match(quickQuestionGroups[3].questions[0], /compleanno/);
});

test('known navigation typos are corrected without guessing ingredients or vegan suitability', async () => {
  assert.match((await requestReply('Vorrei prenottare', { fetchImpl: noNetwork })).reply, /\/prenota/);
  assert.match((await requestReply('Sono vegeteriano', { fetchImpl: noNetwork })).reply, /esigenze vegetariane/);
  const vegan = await requestReply('Avete piatti vegani?', { fetchImpl: noNetwork });
  assert.match(vegan.reply, /chiedi direttamente alla ciurma/);
  assert.doesNotMatch(vegan.reply, /possiamo concordare/);
  const typo = await requestReply('Un coktail col rum', { fetchImpl: menuFetch });
  assert.match(typo.reply, /Drink test A/);
  const unknown = await requestReply('Un cocktail con cocoo', { fetchImpl: menuFetch });
  assert.match(unknown.reply, /Non trovo/);
});

test('category selection and short ingredient follow-ups retain the right menu', async () => {
  const food = await requestReply('Menu da mangiare', { fetchImpl: menuFetch });
  assert.match(food.reply, /Piatto test/);
  assert.doesNotMatch(food.reply, /Drink test/);
  const drink = await requestReply('Menu da bere', { fetchImpl: menuFetch });
  assert.match(drink.reply, /Drink test/);
  const coconut = await requestReply('al cocco?', { context: drink.context, fetchImpl: menuFetch });
  assert.match(coconut.reply, /Drink test A/);
  assert.doesNotMatch(coconut.reply, /Drink test B/);
  assert.deepEqual(coconut.quickReplies, ['E altri?', 'E gli analcolici?', 'E i prezzi?']);
});

test('booking, availability and follow-up details go to the form without an API call', async () => {
  for (const question of ['Vorrei prenotare', 'Avete disponibilità?', 'un tavolo per due', 'Book a table', 'siamo quattro', 'siamo in 4', 'Hai libero stasera?', 'Cancella la prenotazione']) {
    const result = await requestReply(question, { sessionToken: 'old-booking-context', fetchImpl: noNetwork });
    assert.match(result.reply, /\/prenota/);
    assert.match(result.reply, /non confermo/);
    assert.equal(result.sessionToken, null);
  }
  for (const question of ['20:30', 'domani', '4']) {
    const result = await requestReply(question, { context: { topic: 'booking' }, fetchImpl: noNetwork });
    assert.match(result.reply, /\/prenota/);
  }
});

test('dietary variations are agreed by phone or at the restaurant, with staff checking allergens', async () => {
  for (const question of ['Sono celiaco', 'allergia al sesamo', 'Qualcosa senza pollo?', 'gluten free?', 'lattosio']) {
    const result = await requestReply(question, { fetchImpl: noNetwork });
    assert.match(result.reply, /si concordano direttamente al telefono/);
    assert.match(result.reply, /oppure al locale/);
    assert.match(result.reply, /ciurma verifica ingredienti e preparazione/);
    assert.match(result.reply, /non può confermare via chat/);
    assert.match(result.reply, /339 751 4140/);
  }
  for (const question of ['Sono vegetariano', 'Avete variazioni per vegetariani?']) {
    const result = await requestReply(question, { fetchImpl: noNetwork });
    assert.match(result.reply, /esigenze vegetariane/);
    assert.match(result.reply, /direttamente al telefono/);
    assert.match(result.reply, /oppure al locale/);
  }
  const priority = await requestReply('Sono vegetariano e allergico al sesamo', { fetchImpl: noNetwork });
  assert.match(priority.reply, /allergie/);
  assert.match(priority.reply, /ciurma verifica ingredienti/);
});

test('general locale/event questions still use existing chat contract and temporary session', async () => {
  let calls = 0;
  const result = await requestReply('Raccontami del locale', { sessionToken: 'signed-session', fetchImpl: async (url, options) => {
    calls++;
    assert.equal(url, '/api/chat');
    assert.equal(options.method, 'POST');
    assert.equal(options.cache, 'no-store');
    assert.deepEqual(JSON.parse(options.body), { message: 'Raccontami del locale', session_token: 'signed-session' });
    return ok({ reply: 'Ahoy! Ecco le indicazioni del locale.', session_token: 'next-session', quick_replies: ['Orari?', 'Orari?', '', null, 'x'.repeat(121), 'Eventi?'] });
  } });
  assert.equal(calls, 1);
  assert.equal(result.sessionToken, 'next-session');
  assert.deepEqual(result.quickReplies, ['Orari?', 'Eventi?']);
  assert.equal(localReply('Siete aperti oggi?'), null);
});

test('contacts use the existing site data and negated booking intent does not hijack the question', async () => {
  for (const message of ['Dove siete?', 'Come vi raggiungo?', 'Non voglio prenotare, dove siete?']) {
    const result = await requestReply(message, { fetchImpl: noNetwork });
    assert.match(result.reply, /Via Braccio da Montone, 3\/B/);
    assert.match(result.reply, /\/#contatti/);
  }
});

test('an opening-hours reply is preserved even if it contains a time and a booking link', async () => {
  const result = await requestReply('A che ora aprite?', { fetchImpl: async () => ok({ reply: 'Orario di test: dalle 20:30. Per prenotare: /prenotazioni', session_token: 'hours' }) });
  assert.equal(result.reply, 'Orario di test: dalle 20:30. Per prenotare: /prenota');
  assert.equal(result.sessionToken, 'hours');
});

test('a bare number or date asks for clarification without sending booking details upstream', async () => {
  for (const message of ['4', '20:30', 'domani']) assert.match((await requestReply(message, { fetchImpl: noNetwork })).reply, /dettaglio in piu|dettaglio in più/);
});

test('menu recommendations quote only published items matching the requested ingredient', async () => {
  const result = await requestReply('Mi consigli un cocktail con rum?', { fetchImpl: menuFetch });
  assert.match(result.reply, /Drink test A/);
  assert.match(result.reply, /10,50\s*€/);
  assert.match(result.reply, /Rum e cocco/);
  assert.doesNotMatch(result.reply, /Piatto test|Bevanda test|Drink test D/);
  assert.equal(result.context.topic, 'drink');
  assert.deepEqual(result.context.searchTerms, ['rum']);
  assert.equal(result.sessionToken, null);
});

test('contextual follow-ups preserve the topic and switch to the published non-alcoholic category', async () => {
  const first = await requestReply('Mi consigli un cocktail con rum?', { fetchImpl: menuFetch });
  const coconut = await requestReply('E al cocco?', { context: first.context, fetchImpl: menuFetch });
  assert.match(coconut.reply, /Drink test A/);
  assert.doesNotMatch(coconut.reply, /Drink test B/);
  const prices = await requestReply('E i prezzi?', { context: coconut.context, fetchImpl: menuFetch });
  assert.match(prices.reply, /Drink test A/);
  const alcoholFree = await requestReply('E gli analcolici?', { context: first.context, fetchImpl: menuFetch });
  assert.match(alcoholFree.reply, /Bevanda test/);
  assert.doesNotMatch(alcoholFree.reply, /Drink test A/);
  const withoutAlcohol = await requestReply('Un drink senza alcol', { fetchImpl: menuFetch });
  assert.match(withoutAlcohol.reply, /Bevanda test/);
  const ingredients = await requestReply('Quali ingredienti contiene Drink test A?', { fetchImpl: menuFetch });
  assert.match(ingredients.reply, /Rum e cocco/);
});

test('more suggestions continue the same search without repeating the first items', async () => {
  const first = await requestReply('Un cocktail col rum', { fetchImpl: menuFetch });
  const more = await requestReply('E altri?', { context: first.context, fetchImpl: menuFetch });
  assert.match(more.reply, /Drink test D/);
  assert.doesNotMatch(more.reply, /Drink test A/);
  const done = await requestReply('Ancora?', { context: more.context, fetchImpl: menuFetch });
  assert.match(done.reply, /tutte le voci/);
});

test('missing menu items, prices and menu errors never produce guessed values or stale answers', async () => {
  const absent = await requestReply('Un cocktail al mango?', { fetchImpl: menuFetch });
  assert.match(absent.reply, /Non trovo/);
  assert.doesNotMatch(absent.reply, /Drink test A/);
  const missingPrice = await requestReply('Drink test C', { fetchImpl: menuFetch });
  assert.doesNotMatch(missingPrice.reply, /0,00/);
  assert.match(missingPrice.reply, /Drink test C/);
  for (const data of [{}, null, { menu: 'broken' }]) await assert.rejects(requestReply('Un cocktail', { fetchImpl: async () => ok(data) }), error => error.code === 'menu-unavailable');
  await assert.rejects(requestReply('Un cocktail', { fetchImpl: async () => new Response('{}', { status: 503 }) }), error => error.code === 'menu-unavailable');
});

test('menu rate limiting identifies its own request scope', async () => {
  await assert.rejects(requestReply('Un cocktail', { fetchImpl: async () => new Response('', { status: 429, headers: { 'Retry-After': '5' } }) }), error => error.code === 'rate-limit' && error.scope === 'menu' && error.retryAfter === 5);
});

test('cancellation before starting also prevents immediate local answers', async () => {
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(requestReply('Dove siete?', { signal: controller.signal, fetchImpl: noNetwork }), error => error.name === 'AbortError');
});

test('upstream booking and unverified food claims cannot restart the old conversation flow', async () => {
  for (const reply of ['La prenotazione è confermata!', 'Abbiamo tavoli disponibili.', 'Questo piatto costa 12 euro.', 'Sono 25€.', 'Il sushi è senza glutine.', 'È vegano, garantito.']) {
    const result = await requestReply('Raccontami del locale', { fetchImpl: async () => ok({ reply, session_token: 'do-not-retain', quick_replies: ['Conferma'] }) });
    assert.notEqual(result.reply, reply);
    assert.equal(result.sessionToken, null);
    assert.ok(!result.quickReplies.includes('Conferma'));
  }
});

test('rejects invalid input before contacting the API', async () => {
  for (const text of ['', '   ', 'x'.repeat(501)]) await assert.rejects(requestReply(text, { fetchImpl: noNetwork }), error => error.code === 'invalid-input');
});

test('empty, malformed and excessive responses become recoverable errors', async () => {
  for (const data of [null, {}, { reply: '' }, { reply: '   ' }, { reply: 123 }, { reply: 'x'.repeat(8001) }]) {
    await assert.rejects(requestReply('Raccontami del locale', { fetchImpl: async () => ok(data) }));
  }
  await assert.rejects(requestReply('Raccontami del locale', { fetchImpl: async () => new Response('<html>bad gateway</html>') }));
});

test('HTTP and network errors do not leak internal messages or retry automatically', async () => {
  for (const status of [400, 500, 502, 503]) {
    let calls = 0;
    await assert.rejects(requestReply('Raccontami del locale', { fetchImpl: async () => { calls++; return new Response('secret internal detail', { status }); } }), error => {
      assert.doesNotMatch(errorMessage(error), /secret|500|502|503/);
      return true;
    });
    assert.equal(calls, 1);
  }
  await assert.rejects(requestReply('Raccontami del locale', { fetchImpl: async () => { throw new TypeError('network private details'); } }), error => error.code === 'unavailable');
});

test('rate limits preserve Retry-After guidance for the UI cooldown', async () => {
  await assert.rejects(requestReply('Raccontami del locale', { fetchImpl: async () => new Response('', { status: 429, headers: { 'Retry-After': '30' } }) }), error => {
    assert.equal(error.code, 'rate-limit');
    assert.equal(error.retryAfter, 30);
    assert.match(errorMessage(error), /30 secondi/);
    return true;
  });
});

test('timeout aborts a slow request and distinguishes it from user cancellation', async () => {
  const pending = (_url, { signal }) => new Promise((_, reject) => {
    const abort = () => reject(new DOMException('Aborted', 'AbortError'));
    if (signal.aborted) abort(); else signal.addEventListener('abort', abort, { once: true });
  });
  await assert.rejects(requestReply('Raccontami del locale', { timeoutMs: 10, fetchImpl: pending }), error => error.code === 'timeout');
  const controller = new AbortController();
  const result = requestReply('Raccontami del locale', { signal: controller.signal, fetchImpl: pending });
  controller.abort();
  await assert.rejects(result, error => error.name === 'AbortError');
});

test('owner-approved venue answers work without upstream chat and preserve booking and allergy priority', async () => {
  const examples = [
    ['Avete piatti per bambini?', /carne con osso.*udon.*Cestino del Pirata/],
    ['Mi consigli un cocktail poco dolce?', /Hurricane.*Belladonna.*Bourbon Special/],
    ['Posso venire a bere dopo cena?', /23:00.*attendi la conferma/],
    ['Posso portare il cane?', /benvenuto/],
    ['Avete tavoli all’aperto?', /Abbiamo anche tavoli all’aperto/],
    ['Siete accessibili in sedia a rotelle?', /accessibile in sedia a rotelle/],
    ['Quali pacchetti festa proponete?', /Drink \+ torta.*Drink \+ snack.*Drink \+ prosecco/],
    ['Come richiedo un preventivo?', /chiama la ciurma al 339 751 4140/i],
    ['Posso privatizzare il locale?', /339 751 4140.*privatizzazione/],
  ];
  for (const [question, expected] of examples) {
    const result = await requestReply(question, { fetchImpl: noNetwork });
    assert.match(result.reply, expected);
    assert.equal(result.sessionToken, null);
    assert.doesNotMatch(result.reply, /€|euro/);
  }
  assert.match((await requestReply('Prenota un tavolo all’aperto', { fetchImpl: noNetwork })).reply, /non confermo prenotazioni/);
  assert.match((await requestReply('Un piatto per bambini allergici al sesamo', { fetchImpl: noNetwork })).reply, /non può confermare via chat/);
});

test('gluten and lactose variations keep contamination limits and do not override other allergies', async () => {
  const gluten = await requestReply('Avete piatti senza glutine?', { fetchImpl: noNetwork });
  assert.match(gluten.reply, /farina e salsa di soia senza glutine/);
  assert.match(gluten.reply, /assenza di allergeni o contaminazioni/);
  const lactose = await requestReply('Avete piatti senza lattosio?', { fetchImpl: noNetwork });
  assert.match(lactose.reply, /variazioni ai piatti per il lattosio/);
  assert.match(lactose.reply, /verifica ingredienti e preparazione/);
  const both = await requestReply('Senza glutine e senza lattosio', { fetchImpl: noNetwork });
  assert.match(both.reply, /glutine e lattosio/);
  const allergy = await requestReply('Sono celiaco e allergico alla soia', { fetchImpl: noNetwork });
  assert.doesNotMatch(allergy.reply, /Certo/);
  assert.match(allergy.reply, /non può confermare/);
});
