import { useEffect, useRef, useState } from 'react';
import SiteNav from '../components/SiteNav';
import '../styles/prenotazioni.css';

const DINNER_TIMES = ['19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30'];
const AFTER_DINNER_TIMES = ['22:30', '23:00', '23:30', '00:00'];

export default function BookingManagementPage({ containerRef }) {
  const token = useRef(new URLSearchParams(window.location.hash.slice(1)).get('token') || '');
  const operationId = useRef(null);
  const [booking, setBooking] = useState(null);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');
  const [busy, setBusy] = useState(false);
  const [type, setType] = useState('data');
  const [value, setValue] = useState('');

  async function action(kind, extra = {}) {
    const response = await fetch(`/api/booking-management/${kind}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: token.current, ...extra }),
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Richiesta non disponibile.');
    return data;
  }

  useEffect(() => {
    let active = true;
    action('view').then(data => { if (active) setBooking(data); })
      .catch(failure => { if (active) setError(failure.message); });
    return () => { active = false; };
  }, []);

  function changeType(next) {
    setType(next);
    setValue('');
    operationId.current = null;
  }

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    if (type === 'cancellazione' && !window.confirm('Vuoi cancellare questa prenotazione? Il tavolo sarà liberato subito.')) return;
    setBusy(true);
    setError('');
    setFeedback('');
    operationId.current ||= crypto.randomUUID();
    try {
      const result = await action('request', {
        request_type: type,
        requested_value: type === 'cancellazione' ? null : type === 'persone' ? Number(value) : value,
        operation_id: operationId.current,
      });
      setBooking(await action('view'));
      operationId.current = null;
      setFeedback(result.outcome === 'cancelled'
        ? 'Prenotazione cancellata. Il tavolo è stato liberato.'
        : result.outcome === 'applied'
          ? 'Modifica confermata. Abbiamo aggiornato la prenotazione.'
          : result.outcome === 'unchanged'
            ? 'La prenotazione ha già questi dati.'
            : 'Richiesta inviata allo staff. La prenotazione attuale resta confermata.');
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  async function reconfirm() {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      await action('reconfirm');
      setBooking(await action('view'));
      setFeedback('Prenotazione riconfermata. Ti aspettiamo!');
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  const times = booking?.booking_type === 'dopocena' ? AFTER_DINNER_TIMES : DINNER_TIMES;
  return <div ref={containerRef} className="scroll-container booking-page">
    <SiteNav />
    <main className="booking-main">
      <h1 className="section-title">La tua prenotazione</h1>
      {error && <p role="alert">{error}</p>}
      {booking && <section className="booking-card customer-manage-form">
        <h2>Ahoy {booking.name}!</h2>
        <p>{booking.booking_date} · {booking.booking_time?.slice(0, 5)} · {booking.party_size} persone · {booking.booking_type === 'dopocena' ? 'DOPOCENA' : 'CENA'}</p>
        <p>{booking.status === 'confirmed' ? 'Confermata' : booking.status === 'cancelled' ? 'Cancellata' : booking.status}</p>
        {booking.booking_time?.startsWith('00:') && <p>Mezzanotte del giorno successivo alla giornata selezionata.</p>}
        {booking.status === 'confirmed' && <>
          <button className="booking-submit" disabled={busy || booking.reconfirmation_status === 'reconfirmed'} onClick={reconfirm}>
            {booking.reconfirmation_status === 'reconfirmed' ? 'Riconfermata' : 'Riconferma prenotazione'}
          </button>
          <form onSubmit={submit}>
            <label className="booking-field">Cosa vuoi fare?
              <select value={type} onChange={event => changeType(event.target.value)}>
                <option value="data">Cambiare data</option>
                <option value="ora">Cambiare orario</option>
                <option value="persone">Cambiare numero di persone</option>
                <option value="note">Aggiornare le note</option>
                <option value="cancellazione">Cancellare la prenotazione</option>
              </select>
            </label>
            {type !== 'cancellazione' && <label className="booking-field">Nuovo valore
              {type === 'note' ? <textarea maxLength={300} value={value} onChange={event => { setValue(event.target.value); operationId.current = null; }} />
                : type === 'ora' ? <select required value={value} onChange={event => { setValue(event.target.value); operationId.current = null; }}>
                  <option value="">Scegli l’orario</option>
                  {times.map(time => <option key={time} value={time}>{time}</option>)}
                </select>
                  : <input required type={type === 'data' ? 'date' : 'number'} min={type === 'persone' ? 1 : undefined}
                    max={type === 'persone' ? 6 : undefined} value={value}
                    onChange={event => { setValue(event.target.value); operationId.current = null; }} />}
            </label>}
            <p>Se il nuovo orario o tavolo è disponibile, la modifica è immediata. Altrimenti lo staff riceve la richiesta. La cancellazione è immediata.</p>
            <button className="booking-submit" disabled={busy}>{busy ? 'Attendi…' : type === 'cancellazione' ? 'Cancella prenotazione' : 'Conferma'}</button>
          </form>
        </>}
        {feedback && <p role="status">{feedback}</p>}
        {!!booking.requests?.length && <ul>{booking.requests.map(request => <li key={request.id}>
          {request.type} · {String(request.value ?? '')} · {request.status === 'pending' ? 'In attesa' : request.status === 'approved' ? 'Approvata' : 'Rifiutata'}
          {request.alternative && <p>Alternativa dello staff: {request.alternative}. Contatta il locale per concordarla.</p>}
        </li>)}</ul>}
      </section>}
    </main>
  </div>;
}
