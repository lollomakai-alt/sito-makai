import { useRef, useState } from "react";
import usePageMotion from "./hooks/usePageMotion";

import "./styles/index.css";
import "./styles/app.css";
import "./styles/hero.css";
import "./styles/chi-siamo.css";
import "./styles/menu.css";
import "./styles/eventi.css";
import "./styles/galleria.css";
import "./styles/contatti.css";
import "./styles/chat.css";
import "./styles/privacy.css";

import AboutSection from "./components/AboutSection";
import ChatWidget from "./components/ChatWidget";
import ContactsSection from "./components/ContactsSection";
import EventsSection from "./components/EventsSection";
import HeroSection from "./components/HeroSection";
import HomeMenuSection from "./components/HomeMenuSection";
import SiteNav from "./components/SiteNav";
import { menuPages } from "./data/siteContent";
import AboutPage from "./pages/AboutPage";
import GalleryPage from "./pages/GalleryPage";
import MenuDetailPage from "./pages/MenuDetailPage";
import Privacy from "./pages/Privacy";

function App() {
  const containerRef = useRef(null);
  const [activeSection] = useState("Chi siamo");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [startBooking, setStartBooking] = useState(false);

  const currentPath = window.location.pathname.replace(/\/$/, "") || "/";
  const menuPage = menuPages[currentPath];
  const isGalleryPage = currentPath === "/galleria";
  const isAboutPage = currentPath === "/chi-siamo";
  const isPrivacyPage = currentPath === "/privacy";

  usePageMotion(containerRef, currentPath);

  function openBookingChat() {
    setStartBooking(true);
    setIsChatOpen(true);
  }

  function closeChat() {
    setIsChatOpen(false);
    setStartBooking(false);
  }

  if (isGalleryPage) {
    return <GalleryPage containerRef={containerRef} />;
  }

  if (isAboutPage) {
    return <AboutPage containerRef={containerRef} />;
  }

  if (isPrivacyPage) {
    return <Privacy />;
  }

  if (menuPage) {
    return <MenuDetailPage containerRef={containerRef} page={menuPage} />;
  }

  return (
    <div ref={containerRef} className="scroll-container">
      <SiteNav activeSection={activeSection} />

      <main className="main-content">
        <HeroSection />
        <AboutSection />
        <HomeMenuSection />
        <EventsSection />
        <ContactsSection onOpenChat={openBookingChat} />
      </main>

      <ChatWidget
        isOpen={isChatOpen}
        startBooking={startBooking}
        onOpen={() => setIsChatOpen(true)}
        onClose={closeChat}
      />
    </div>
  );
}

export default App;
