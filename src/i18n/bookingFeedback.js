const choose = (language, it, en) => language === 'en' ? en : it;

export function receiptMessage(receipt, { guests, time, date, language = 'it' }) {
  const summary = choose(language, `${date} per ${guests} persone alle ${time}`, `${date} for ${guests} guests at ${time}`);
  switch (receipt.status) {
    case 'confirmed': return choose(language, `Ahoy, prenotazione confermata! Ti aspettiamo a bordo il ${summary}.`, `Ahoy, booking confirmed! We look forward to welcoming you aboard on ${summary}.`);
    case 'pending': return choose(language, `Messaggio ricevuto dalla ciurma! Richiesta DOPOCENA per il ${summary}. È in attesa di verifica: la prenotazione non è ancora confermata.`, `The crew has received your request! DOPOCENA on ${summary}. It is awaiting review: your booking is not confirmed yet.`);
    case 'accepted': return choose(language, 'Ahoy! La ciurma ha accettato la richiesta DOPOCENA. Questo esito non indica un tavolo assegnato. Per i dettagli contatta il locale.', 'Ahoy! The crew has accepted your DOPOCENA request. This does not indicate an assigned table. Contact the venue for details.');
    case 'rejected': return choose(language, 'La ciurma non ha potuto accettare la richiesta DOPOCENA. Per valutare un’altra rotta, contatta il locale.', 'The crew could not accept your DOPOCENA request. Contact the venue to explore another course.');
    case 'cancelled': return choose(language, 'La prenotazione risulta cancellata nel registro di bordo. Per una nuova serata, avvia una nuova prenotazione.', 'The ship’s log shows this booking as cancelled. Start a new booking to plan another evening.');
    default: return choose(language, 'La ciurma non può confermare l’esito di questa richiesta. Contatta il locale prima di considerarla confermata.', 'The crew cannot confirm the outcome of this request. Contact the venue before treating it as confirmed.');
  }
}

export function managementMessage(outcome, language = 'it') {
  const messages = {
    cancelled: ['Prenotazione cancellata nel registro di bordo. Se era assegnato un tavolo, ora è stato liberato.', 'Booking cancelled in the ship’s log. If a table was assigned, it has now been released.'],
    applied: ['Rotta aggiornata! La modifica alla prenotazione è confermata.', 'Course updated! The booking change is confirmed.'],
    unchanged: ['Tutto già in rotta: la prenotazione ha già questi dati. Nessuna modifica necessaria.', 'All on course: the booking already has these details. No change was needed.'],
    pending: ['Richiesta ricevuta dalla ciurma, in attesa di verifica. La modifica non è ancora confermata; la prenotazione attuale resta invariata e confermata.', 'The crew has received your request for review. The change is not confirmed yet; your current booking remains unchanged and confirmed.'],
  };
  return choose(language, ...(messages[outcome] || [
    'La ciurma non può confermare l’esito della modifica. Aggiorna la pagina o contatta il locale per verificare la prenotazione.',
    'The crew cannot confirm the change outcome. Refresh the page or contact the venue to check your booking.',
  ]));
}

export function bookingStatusLabel(status, language = 'it') {
  const labels = {
    confirmed: ['Confermata', 'Confirmed'],
    cancelled: ['Cancellata', 'Cancelled'],
    arrived: ['Cliente arrivato', 'Guest arrived'],
    completed: ['Conclusa', 'Completed'],
    no_show: ['Cliente non arrivato', 'No-show'],
  };
  return choose(language, ...(labels[status] || ['Stato da verificare', 'Status to be checked']));
}

export function requestTypeLabel(type, language = 'it') {
  const labels = {
    data: ['Cambio data', 'Date change'],
    ora: ['Cambio orario', 'Time change'],
    persone: ['Cambio persone', 'Guest count change'],
    note: ['Aggiornamento note', 'Notes update'],
    cancellazione: ['Cancellazione', 'Cancellation'],
  };
  return choose(language, ...(labels[type] || ['Richiesta', 'Request']));
}

export function requestStatusLabel(status, language = 'it') {
  const labels = {
    pending: ['In attesa di verifica', 'Awaiting review'],
    approved: ['Approvata', 'Approved'],
    rejected: ['Rifiutata', 'Declined'],
  };
  return choose(language, ...(labels[status] || ['Stato da verificare', 'Status to be checked']));
}

const knownErrors = {
  'Collegamento non valido o scaduto.': 'This booking link is invalid or expired.',
  'Collegamento non valido o prenotazione non riconfermabile.': 'This booking link is invalid, expired, or can no longer be reconfirmed.',
  'Collegamento non valido o prenotazione non modificabile.': 'This booking link is invalid, expired, or the booking can no longer be changed.',
  'Richiesta non disponibile. Aggiorna la pagina o contatta il locale.': 'This request is unavailable. Refresh the page or contact the venue.',
  'Servizio momentaneamente non disponibile.': 'The service is temporarily unavailable.',
  'Prenotazione non più modificabile': 'This booking can no longer be changed.',
  'Data, orario o coperti non validi': 'The date, time, or guest count is invalid.',
  'Data non valida': 'The date is invalid.',
  'Ora non valida': 'The time is invalid.',
  'Numero persone non valido': 'The guest count is invalid.',
  'Valore richiesta non valido': 'The requested value is invalid.',
  'Note troppo lunghe': 'The notes are too long.',
  'Identificativo operazione mancante': 'The operation could not be identified. Refresh the page and try again.',
  'Identificativo operazione già utilizzato': 'This operation has already been used. Refresh the page to check its outcome.',
  'Richiesta incompleta.': 'Some request details are missing. Refresh the page and try again.',
  'Richiesta non disponibile.': 'This request is unavailable. Contact the venue if the issue continues.',
};

export function formError(error, language = 'it') {
  const technical = error instanceof TypeError || error instanceof SyntaxError || ['AbortError', 'TimeoutError'].includes(error?.name);
  const rawDetail = error?.message || String(error || '');
  const englishDetail = knownErrors[rawDetail] || rawDetail;
  const detail = technical ? choose(language, 'Risposta non ricevuta o non leggibile. L’esito dell’operazione non è verificato: controlla la prenotazione o contatta il locale prima di riprovare.', 'The response was not received or could not be read. The outcome is unverified: check your booking or contact the venue before retrying.') : choose(language, rawDetail, englishDetail);
  return choose(language, `Un intoppo sulla rotta. ${detail}`, `A snag on our course. ${detail}`);
}

// Keep native validity constraints; replace only the customer-facing explanation.
export function explainInvalidInput(event, language = 'it') {
  const input = event.target;
  input.setCustomValidity('');
  const v = input.validity;
  if (v.valid) return;
  let message;
  if (v.valueMissing) message = input.name === 'privacy'
    ? choose(language, 'Prima di salpare, conferma di aver letto l’informativa privacy. Il marketing resta facoltativo.', 'Before setting sail, confirm you have read the privacy policy. Marketing remains optional.')
    : choose(language, 'Manca un dato a bordo: compila questo campo per proseguire.', 'A detail is missing aboard: complete this field to continue.');
  else if (v.typeMismatch && input.type === 'email') message = choose(language, 'Controlla la rotta della tua email: inserisci un indirizzo valido.', 'Check your email’s course: enter a valid address.');
  else if (v.tooShort) message = choose(language, `Mancano lettere nel registro: inserisci almeno ${input.minLength} caratteri.`, `The log needs more letters: enter at least ${input.minLength} characters.`);
  else if (v.rangeUnderflow || v.rangeOverflow) message = choose(language, `Controlla la ciurma: inserisci un numero tra ${input.min} e ${input.max}.`, `Check your crew: enter a number between ${input.min} and ${input.max}.`);
  else message = choose(language, 'Controlla questo dato nel registro di bordo e correggilo per proseguire.', 'Check this detail in the ship’s log and correct it to continue.');
  input.setCustomValidity(message);
}

export function clearInputExplanation(event) {
  event.target.setCustomValidity?.('');
}
