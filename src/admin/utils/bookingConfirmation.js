export function confirmationMessage(booking) {
  const [year, month, day] = booking.booking_date.split("-");
  return `Ciao ${booking.name}!\n\nTi confermiamo la prenotazione al Makai Grand Line Pigneto:\n\nNome: ${booking.name}\nData: ${day}/${month}/${year}\nOra: ${booking.booking_time.slice(0, 5)}\nPersone: ${booking.party_size}\n\nTi aspettiamo!`;
}

export function confirmationUrl(booking) {
  if (booking.status !== "confirmed") return null;
  let phone = String(booking.phone || "").trim().replace(/[\s().-]/g, "");
  if (phone.startsWith("00")) phone = `+${phone.slice(2)}`;
  // Come nel backend, riconosciamo i cellulari italiani senza prefisso.
  if (/^3[0-9]{8,9}$/.test(phone)) phone = `+39${phone}`;
  if (!/^\+[1-9][0-9]{5,14}$/.test(phone)) return null;
  return `https://wa.me/${phone.slice(1)}?text=${encodeURIComponent(confirmationMessage(booking))}`;
}
