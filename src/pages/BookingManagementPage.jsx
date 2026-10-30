import { useEffect, useRef, useState } from 'react';
import { managementMessage, bookingStatusLabel, requestTypeLabel, requestStatusLabel, formError, explainInvalidInput, clearInputExplanation } from '../i18n/bookingFeedback';
import SiteNav from '../components/SiteNav';
import SiteHeading from '../components/SiteHeading';
import { useLanguage } from '../i18n/LanguageContext';
import '../styles/prenotazioni.css';

const DINNER_TIMES = ['19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30'];
const AFTER_DINNER_TIMES = ['23:00', '23:30', '00:00'];

export default function BookingManagementPage({ containerRef }) {
  const { language } = useLanguage();
  const t = (it, en) => language === 'en' ? en : it;
  const locale = language === 'en' ? 'en-GB' : 'it-IT';
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
      .catch(failure => { if (active) setError(failure); });
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
    if (type === 'cancellazione' && !window.confirm(t('Vuoi cancellare la prenotazione dal registro di bordo? La cancellazione è immediata; un eventuale tavolo assegnato sarà liberato.', 'Cancel this booking from the ship’s log? Cancellation is immediate; any assigned table will be released.'))) return;
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
      setFeedback(managementMessage(result.outcome, language));
    } catch (failure) {
      setError(failure);
    } finally {
      setBusy(false);
    }
  }

  async function reconfirm() {
    if (busy) return;
    setBusy(true);
    setError('');
    setFeedback('');
    try {
      await action('reconfirm');
      setBooking(await action('view'));
      setFeedback(t('Presenza riconfermata nel registro di bordo. La ciurma ti aspetta!', 'Your attendance is reconfirmed in the ship’s log. The crew looks forward to seeing you!'));
    } catch (failure) {
      setError(failure);
    } finally {
      setBusy(false);
    }
  }

  const times = booking?.booking_type === 'dopocena' ? AFTER_DINNER_TIMES : DINNER_TIMES;
  return <div ref={containerRef} className="scroll-container booking-page">
    <SiteNav />
    <main className="booking-main">
      <SiteHeading as="h1" className="section-title">{t("La tua prenotazione", "Your booking")}</SiteHeading>
      {error && <p role="alert">{formError(error, language)}</p>}
      {booking && <section className="booking-card customer-manage-form">
        <h2>Ahoy {booking.name}!</h2>
        <p>{new Date(`${booking.booking_date}T12:00:00`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })} · {booking.booking_time?.slice(0, 5)} · {booking.party_size} {t('persone', 'guests')} · {booking.booking_type === 'dopocena' ? 'DOPOCENA' : 'CENA'}</p>
        <p>{bookingStatusLabel(booking.status, language)}</p>
        {booking.booking_time?.startsWith('00:') && <p>{t('Mezzanotte del giorno successivo alla giornata selezionata.', 'Midnight at the end of the selected service day.')}</p>}
        {booking.status === 'confirmed' && <>
          <button className="booking-submit" disabled={busy || booking.reconfirmation_status === 'reconfirmed'} onClick={reconfirm}>
            {booking.reconfirmation_status === 'reconfirmed' ? t('Presenza riconfermata', 'Attendance reconfirmed') : t('Riconferma la tua presenza', 'Reconfirm your attendance')}
          </button>
          <form onInvalid={explainInvalidInput} onInput={clearInputExplanation} onSubmit={submit}>
            <label className="booking-field">{t("Cosa vuoi fare?", "What would you like to change?")}
              <select value={type} onChange={event => changeType(event.target.value)}>
                <option value="data">{t("Cambiare data", "Change date")}</option>
                <option value="ora">{t("Cambiare orario", "Change time")}</option>
                <option value="persone">{t("Cambiare numero di persone", "Change number of guests")}</option>
                <option value="note">{t("Aggiornare le note", "Update notes")}</option>
                <option value="cancellazione">{t("Cancellare la prenotazione", "Cancel booking")}</option>
              </select>
            </label>
            {type !== 'cancellazione' && <label className="booking-field">{t("Nuovo valore", "New value")}
              {type === 'note' ? <textarea maxLength={300} value={value} onChange={event => { setValue(event.target.value); operationId.current = null; }} />
                : type === 'ora' ? <select required value={value} onChange={event => { setValue(event.target.value); operationId.current = null; }}>
                  <option value="">{t("Scegli l’orario", "Choose a time")}</option>
                  {times.map(time => <option key={time} value={time}>{time}</option>)}
                </select>
                  : <input required type={type === 'data' ? 'date' : 'number'} min={type === 'persone' ? 1 : undefined}
                    max={type === 'persone' ? 6 : undefined} value={value}
                    onChange={event => { setValue(event.target.value); operationId.current = null; }} />}
            </label>}
            <p>{t("Le note si aggiornano subito. Per data, orario e persone, la modifica è immediata se disponibile; altrimenti la ciurma riceve una richiesta da verificare e la prenotazione attuale resta invariata. La cancellazione è immediata.", "Notes update immediately. Date, time, and guest count changes apply immediately when available; otherwise the crew receives a request to review and your current booking stays unchanged. Cancellation is immediate.")}</p>
            <button className="booking-submit" disabled={busy}>{busy ? t('Consulto il registro di bordo…', 'Checking the ship’s log…') : type === 'cancellazione' ? t('Cancella prenotazione', 'Cancel booking') : t('Invia modifica', 'Submit change')}</button>
          </form>
        </>}
        {feedback && <p role="status">{feedback}</p>}
        {!!booking.requests?.length && <ul>{booking.requests.map(request => <li key={request.id}>
          {requestTypeLabel(request.type, language)} · {String(request.value ?? '')} · {requestStatusLabel(request.status, language)}
          {request.alternative && <p>{t('Nuova rotta proposta dalla ciurma:', 'A new course proposed by the crew:')} {request.alternative}. {t('Contatta il locale per concordarla.', 'Contact the venue to discuss it.')}</p>}
        </li>)}</ul>}
      </section>}
    </main>
  </div>;
}
