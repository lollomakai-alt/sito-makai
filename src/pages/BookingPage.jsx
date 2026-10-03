import { useEffect, useRef, useState } from "react";
import SiteNav from "../components/SiteNav";
import { useLanguage } from "../i18n/LanguageContext";
import "../styles/prenotazioni.css";

// Availability is read-only. This page never saves bookings or consent.
export default function BookingPage({ containerRef }) {
  const { language } = useLanguage();
  const t = (it, en) => language === "en" ? en : it;
  const locale = language === "en" ? "en-GB" : "it-IT";
  const [today] = useState(() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; });
  const [monthOffset, setMonthOffset] = useState(0);
  const [guests, setGuests] = useState(2);
  const [selected, setSelected] = useState(null);
  const [reviewed, setReviewed] = useState(false);
  const [settings, setSettings] = useState(null);
  const [settingsError, setSettingsError] = useState(false);
  const [confirmedGuests, setConfirmedGuests] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [availabilityError, setAvailabilityError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [requestVersion, setRequestVersion] = useState(0);
  const calendarRef = useRef(null);
  const scrollPending = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 10000);
    let active = true;
    fetch("/api/booking-settings", { signal: controller.signal })
      .then(response => { if (!response.ok) throw new Error("Settings unavailable"); return response.json(); })
      .then(data => {
        if (!Number.isInteger(data.max_party_size) || data.max_party_size < 1 || typeof data.phone !== "string") throw new Error("Invalid settings");
        if (active) setSettings(data);
      })
      .catch(() => { if (active) setSettingsError(true); })
      .finally(() => window.clearTimeout(timeout));
    return () => { active = false; controller.abort(); window.clearTimeout(timeout); };
  }, []);
  const largeGroup = settings && guests > settings.max_party_size;
  const phoneHref = settings?.phone ? `tel:${settings.phone.replace(/[^+0-9]/g, "")}` : null;
  useEffect(() => { setSelected(null); setReviewed(false); setConfirmedGuests(null); }, [guests]);
  const month = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
  const days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const blanks = (month.getDay() + 6) % 7;
  const formatDate = (date) => date.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const monthKey = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`;
  const calendarVisible = confirmedGuests === guests && !largeGroup;
  const requestKey = `${monthKey}:${guests}:${requestVersion}`;
  const currentAvailability = calendarVisible && availability?.key === requestKey ? availability : null;
  const dateKey = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  const status = date => currentAvailability?.days[dateKey(date)] || "unverified";
  const horizon = new Date(today); horizon.setDate(horizon.getDate() + (settings?.max_advance_days || 0));
  const lastMonthOffset = (horizon.getFullYear() - today.getFullYear()) * 12 + horizon.getMonth() - today.getMonth();
  useEffect(() => {
    if (!calendarVisible) return undefined;
    const controller = new AbortController();
    let active = true;
    const timer = window.setTimeout(() => controller.abort(), 15000);
    setLoading(true); setAvailabilityError(false); setSelected(null); setReviewed(false);
    if (scrollPending.current) {
      scrollPending.current = false;
      calendarRef.current?.focus({ preventScroll: true });
      calendarRef.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    }
    fetch(`/api/booking-availability?month=${monthKey}&party_size=${confirmedGuests}`, { signal: controller.signal, cache: "no-store" })
      .then(response => { if (!response.ok) throw new Error("Availability unavailable"); return response.json(); })
      .then(data => {
        if (data.month !== monthKey || data.party_size !== confirmedGuests || !Array.isArray(data.days)) throw new Error("Invalid availability");
        if (active) setAvailability({ key: requestKey, days: Object.fromEntries(data.days.map(day => [day.date, day.status])) });
      })
      .catch(() => { if (active) { setAvailability(null); setAvailabilityError(true); } })
      .finally(() => { window.clearTimeout(timer); if (active) setLoading(false); });
    return () => { active = false; controller.abort(); window.clearTimeout(timer); };
  }, [calendarVisible, confirmedGuests, monthKey, requestKey]);
  function showAvailability() {
    setSelected(null); setReviewed(false); scrollPending.current = true;
    setConfirmedGuests(guests); setRequestVersion(value => value + 1);
  }
  const labels = { closed: t("Chiuso", "Closed"), outside_window: t("Non ancora prenotabile", "Outside booking window"), unverified: t("Disponibilità da verificare", "Availability unverified"), past: t("Data passata", "Past date"), full: t("Non disponibile per il gruppo", "Unavailable for your group"), available: t("Disponibile", "Available") };

  return (
    <div ref={containerRef} className="scroll-container booking-page">
      <SiteNav />
      <main className="booking-main">
        <header className="booking-intro">
          <a className="booking-back" href="/#contatti">{t("← Torna ai contatti", "← Back to contacts")}</a>
          <h1 className="section-title">{t("Un posto per te", "A place for you")}</h1>
          <p className="booking-subtitle-panel">{t("La tua prossima serata al Makai inizia qui. Scegli le persone e il giorno, poi lasciaci i tuoi contatti.", "Your next evening at Makai starts here. Choose your party size and date, then leave your contact details.")}</p>
        </header>
        <form className="booking-layout" onChange={() => setReviewed(false)} onSubmit={(event) => { event.preventDefault(); setReviewed(true); }}>
          <div className="booking-card">
            <section aria-labelledby="booking-guests-title">
              <h2 id="booking-guests-title"><span>01</span> {t("Quante persone siete?", "How many guests?")}</h2>
              <div className="booking-guest-stepper" role="group" aria-labelledby="booking-guests-title">
                <button type="button" disabled={guests <= 1} aria-label={t("Una persona in meno", "Remove one guest")} onClick={() => { setGuests(value => Math.max(1, value - 1)); setReviewed(false); }}>−</button>
                <output aria-live="polite" aria-label={t("Numero di persone", "Party size")}>{guests}</output>
                <button type="button" disabled={guests >= 99} aria-label={t("Una persona in più", "Add one guest")} onClick={() => { setGuests(value => Math.min(99, value + 1)); setReviewed(false); }}>+</button>
              </div>
              {!largeGroup && <button type="button" className="booking-submit" onClick={showAvailability} disabled={!settings || loading && calendarVisible}>
                {t("Conferma persone e mostra disponibilità", "Confirm guests and show availability")}
              </button>}
              {largeGroup && <div className="booking-group-notice" role="status">
                <h3>{t("Siete un bel gruppo!", "Planning for a group?")}</h3>
                <p>{t(`Per più di ${settings.max_party_size} persone è meglio chiamarci: troviamo insieme la soluzione più adatta alla vostra serata.`, `For more than ${settings.max_party_size} guests, please call us so we can plan your evening together.`)}</p>
                {phoneHref && <a className="booking-back" href={phoneHref}>{t("Chiamaci", "Call us")} · {settings.phone}</a>}
              </div>}
              {settingsError && <p className="booking-help" role="status">{t("Servizio momentaneamente non disponibile. Riprova più tardi o visita la sezione Contatti.", "Service temporarily unavailable. Try later or visit Contacts.")}</p>}
            </section>
            {calendarVisible && <section ref={calendarRef} tabIndex={-1} className="booking-calendar" aria-labelledby="booking-date-title" aria-busy={loading}>
              <h2 id="booking-date-title"><span>02</span> {t("Scegli il giorno", "Choose a date")}</h2>
              <p className="booking-help" role="status">{loading ? t("Controllo le date disponibili…", "Checking available dates…") : t(`Disponibilità per ${confirmedGuests} persone, senza turni.`, `Availability for ${confirmedGuests} guests, without sittings.`)}</p>
              {availabilityError && <div role="alert" className="booking-help">{t("Non riesco a verificare l’agenda. Nessuna data è confermata disponibile.", "Unable to check availability. No date is confirmed available.")} <button type="button" onClick={showAvailability}>{t("Riprova", "Retry")}</button></div>}
              <div className="booking-month">
                <button type="button" disabled={monthOffset === 0} onClick={() => setMonthOffset(monthOffset - 1)} aria-label={t("Mese precedente", "Previous month")}>←</button>
                <h3 aria-live="polite">{month.toLocaleDateString(locale, { month: "long", year: "numeric" })}</h3>
                <button type="button" disabled={monthOffset >= lastMonthOffset} onClick={() => setMonthOffset(monthOffset + 1)} aria-label={t("Mese successivo", "Next month")}>→</button>
              </div>
              <div className="booking-days">
                {t(["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]).map(day => <span className="booking-weekday" key={day}>{day}</span>)}
                {Array.from({ length: blanks }, (_, index) => <span key={`blank-${index}`} />)}
                {Array.from({ length: days }, (_, index) => {
                  const date = new Date(month.getFullYear(), month.getMonth(), index + 1);
                  const state = status(date);
                  const active = selected?.getTime() === date.getTime();
                  return <button key={index} type="button" className={`booking-day ${state}`} disabled={loading || !currentAvailability || state !== "available"} aria-pressed={active} aria-label={`${formatDate(date)}: ${labels[state]}`} onClick={() => { setSelected(date); setReviewed(false); }}><b>{index + 1}</b><span aria-hidden="true">{active ? "✓" : state === "available" ? "•" : state === "full" ? "×" : "–"}</span></button>;
                })}
              </div>
              <div className="booking-legend"><span>🟢 {t("Disponibile", "Available")}</span><span>🔴 {t("Non disponibile per il gruppo", "Unavailable for your group")}</span><span>— {t("Chiuso / non prenotabile", "Closed / unavailable")}</span></div>
              {currentAvailability && !Object.values(currentAvailability.days).includes("available") && <p className="booking-help">{t("Nessuna data disponibile in questo mese per il vostro gruppo. Controlla il mese successivo o chiamaci.", "No dates available this month for your group. Check the next month or call us.")}</p>}
              <p className="booking-date-feedback" aria-live="polite">{selected ? formatDate(selected) : ""}</p>
            </section>}
          </div>
          {calendarVisible && selected && currentAvailability && !loading && <div className="booking-card">
            <h2><span>03</span> {t("I tuoi contatti", "Your contact details")}</h2>
            <div className="booking-fields">
              <label className="booking-field">{t("Nome", "Name")} *<input name="name" autoComplete="given-name" required maxLength="80" placeholder={t("Come ti chiami?", "Your name")} /></label>
              <label className="booking-field">{t("Telefono", "Phone")} *<input name="phone" type="tel" autoComplete="tel" required maxLength="30" placeholder="+39 …" /></label>
              <label className="booking-field">{t("Note (facoltative)", "Notes (optional)")}<textarea name="notes" rows="3" maxLength="500" /></label>
            </div>
            <p className="booking-help">{t("Non inserire informazioni sulla salute nelle note. I campi con * sono obbligatori.", "Do not include health information in the notes. Fields marked * are required.")}</p>
            <label className="booking-check booking-privacy"><input type="checkbox" required name="privacy" /><span>{t("Ho letto l’", "I have read the ")}<a href="/privacy" target="_blank" rel="noopener noreferrer">{t("informativa privacy", "privacy policy")}</a> * <small>{t("(si apre in una nuova scheda)", "(opens in a new tab)")}</small></span></label>
            <section className="booking-offers" aria-labelledby="booking-offers-title">
              <h2 id="booking-offers-title">{t("SCONTI E OFFERTE ESCLUSIVE", "EXCLUSIVE DISCOUNTS & OFFERS")}</h2>
              <label className="booking-check"><input type="checkbox" name="marketing" /><span>{t("Voglio ricevere sconti, offerte e novità di Makai tramite WhatsApp.", "I would like to receive Makai discounts, offers and news via WhatsApp.")}</span></label>
              <p className="booking-help">{t("Facoltativo. Puoi prenotare anche senza aderire.", "Optional. You can book without opting in.")}</p>
            </section>
            <div className="booking-summary">
              <h2>{t("Il tuo riepilogo", "Your summary")}</h2>
              <p>{guests || "—"} {t("persone", "guests")} · {selected ? formatDate(selected) : t("Data da scegliere", "Choose a date")}</p>
              <button className="booking-submit" type="submit" disabled={!settings || !selected}>{t("Mostra riepilogo", "Show summary")}</button>
              {reviewed && <p className="booking-result" role="status">{t("Hai consultato la disponibilità. Nessuna prenotazione o consenso è stato registrato. Per confermare, chiamaci al", "Availability checked. No booking or consent was recorded. To confirm, call us on")} <a href={phoneHref}>{settings?.phone}</a>.</p>}
            </div>
          </div>}
        </form>
      </main>
    </div>
  );
}
