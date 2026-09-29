import { useEffect, useState } from "react";
import { dayLabel, isDay, todayInRome } from "../utils/calendar";
import { confirmationMessage, confirmationUrl } from "../utils/bookingConfirmation";

export default function BookingsPage() {
  const requested = new URLSearchParams(window.location.search).get("date");
  const date = isDay(requested) ? requested : todayInRome();
  const [bookings, setBookings] = useState(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setBookings(null);
    setError("");
    async function load() {
      try {
        const response = await fetch(`/api/admin/bookings?date=${date}`, {
          credentials: "same-origin", cache: "no-store", signal: controller.signal,
        });
        if (response.status === 401) { window.location.replace("/admin/login"); return; }
        if (!response.ok) throw new Error("Non è stato possibile caricare le prenotazioni. Riprova.");
        const data = await response.json();
        if (!controller.signal.aborted) setBookings(data.bookings);
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message || "Connessione non disponibile.");
      }
    }
    load();
    return () => controller.abort();
  }, [date, refresh]);
  const covers = bookings?.filter((booking) => booking.status === "confirmed")
    .reduce((sum, booking) => sum + booking.party_size, 0);

  const timeGroups = Object.entries((bookings || []).reduce((groups, booking) => {
    const time = booking.booking_time.slice(0, 5);
    (groups[time] ||= []).push(booking);
    return groups;
  }, {})).sort(([first], [second]) => first.localeCompare(second));

  return (
    <main className="booking-admin">
      <a href={`/admin/prenotazioni?month=${date.slice(0, 7)}`}>← Torna al mese</a>
      <div className="agenda-heading">
        <div><p className="agenda-eyebrow">Agenda del giorno</p><h1>{dayLabel(date)}</h1></div>
      </div>
      <div className="day-summary" aria-live="polite">
        <span>{bookings ? <><strong>{covers}</strong> coperti confermati</> : error ? "Coperti non disponibili" : "Caricamento…"}</span>
        <button className="admin-button" type="button" disabled={!bookings && !error} onClick={() => setRefresh((value) => value + 1)}>Aggiorna</button>
      </div>
      {error && <p role="alert">{error}</p>}
      <div aria-live="polite">
        {bookings?.length === 0 && <p>Nessuna prenotazione per questa data.</p>}
        {bookings && bookings.length > 0 && <p>{bookings.length} prenotazioni trovate.</p>}
      </div>
      <div className="booking-time-groups">
        {timeGroups.map(([time, group]) => (
          <section key={time} className="booking-time-group" aria-labelledby={`time-${time}`}>
            <h2 id={`time-${time}`} className="booking-time-heading">
              <span aria-hidden="true">🕒</span> <time>{time}</time>
            </h2>
            <div className="booking-time-list">
              {group.map((booking) => {
                const url = confirmationUrl(booking);
                const confirmed = booking.status === "confirmed";
                return (
                  <article key={booking.id} className={`booking-row${confirmed ? "" : " is-cancelled"}`}>
                    <div className="booking-row-main">
                      <span className="booking-row-covers"><span aria-hidden="true">👥</span><span className="admin-sr-only">Coperti: </span><strong>{booking.party_size}</strong></span>
                      <h3 className="booking-row-name"><span aria-hidden="true">👤</span><span className="admin-sr-only">Nome: </span>{booking.name}</h3>
                      <span className="booking-row-phone"><span aria-hidden="true">📞</span><span className="admin-sr-only">Telefono: </span>{booking.phone || "Non presente"}</span>
                      <span className={`booking-status${confirmed ? "" : " is-cancelled"}`}>{confirmed ? "Confermata" : "Annullata"}</span>
                    </div>
                    {confirmed && <div className="booking-whatsapp-action">
                      {url ? <a className="booking-whatsapp" href={url} target="_blank" rel="noopener noreferrer"
                        aria-label={`Prepara conferma WhatsApp per ${booking.name}`} title="Prepara la conferma: l’invio resta manuale">
                        WhatsApp ↗
                      </a> : <>
                        <button className="booking-whatsapp" type="button" disabled aria-describedby={`phone-help-${booking.id}`}>WhatsApp ↗</button>
                        <small id={`phone-help-${booking.id}`}>{booking.phone ? "Telefono non valido" : "Telefono mancante"}</small>
                      </>}
                    </div>}
                    <details className="booking-row-details">
                      <summary>Dettagli{booking.notes ? " · note" : ""}{confirmed ? " e messaggio" : ""}</summary>
                      <p>Tavoli: {booking.tables || "Non assegnati"}</p>
                      {booking.notes && <p>Note: {booking.notes}</p>}
                      {confirmed && <>
                        <p className="booking-confirmation-preview">{confirmationMessage(booking)}</p>
                        <small>{url ? "Il messaggio si apre pronto da inviare. Premi Invio su WhatsApp per spedirlo." : "Serve un numero valido con prefisso internazionale per aprire WhatsApp."}</small>
                      </>}
                    </details>
                  </article>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}
