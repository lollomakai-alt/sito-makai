import AdminAccess from "./components/AdminAccess";
import LogoutButton from "./components/LogoutButton";
import BookingsPage from "./pages/BookingsPage";
import CalendarPage from "./pages/CalendarPage";
import LoginPage from "./pages/LoginPage";
import "./styles/admin.css";

export default function AdminApp() {
  const path = window.location.pathname.replace(/\/$/, "") || "/admin";
  const isCalendarPage = path === "/admin/prenotazioni";
  let page = <LoginPage />;
  if (isCalendarPage) page = <AdminAccess><CalendarPage /></AdminAccess>;
  if (path === "/admin/prenotazioni/giorno") page = <AdminAccess><BookingsPage /></AdminAccess>;

  return <div className="admin-shell">
    <header className="admin-header">
      <a href="/admin/prenotazioni" className="admin-brand">Makai <span>Agenda</span></a>
      <div className="admin-header-actions">
        <span className="admin-area-label">Area riservata</span>
        {isCalendarPage && <LogoutButton />}
      </div>
    </header>
    {page}
  </div>;
}
