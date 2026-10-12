import { lazy, Suspense, useRef, useState } from "react";
import usePageMotion from "./hooks/usePageMotion";

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
import { getMenuPage } from "./data/siteContent";
import { LanguageProvider, useLanguage } from "./i18n/LanguageContext";
const AboutPage = lazy(() => import("./pages/AboutPage"));
const GalleryPage = lazy(() => import("./pages/GalleryPage"));
const MenuDetailPage = lazy(() => import("./pages/MenuDetailPage"));
const Privacy = lazy(() => import("./pages/Privacy"));
const BookingPage = lazy(() => import("./pages/BookingPage"));

function PageFallback() {
  return (
    <main
      aria-live="polite"
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
        color: "#e8bd62",
        fontFamily: "Georgia, 'Times New Roman', serif",
        textAlign: "center",
      }}
    >
      Caricamento…
    </main>
  );
}

function AppContent() {
  const containerRef = useRef(null);
  const { language } = useLanguage();
  const [activeSection] = useState("about");
  const [isChatOpen, setIsChatOpen] = useState(false);

  const currentPath = window.location.pathname.replace(/\/$/, "") || "/";
  const menuPage = getMenuPage(currentPath, language);
  const isGalleryPage = currentPath === "/galleria";
  const isAboutPage = currentPath === "/chi-siamo";
  const isPrivacyPage = currentPath === "/privacy";

  usePageMotion(containerRef, currentPath);

  function closeChat() {
    setIsChatOpen(false);
  }

  let page = null;
  if (isGalleryPage) page = <GalleryPage containerRef={containerRef} />;
  else if (isAboutPage) page = <AboutPage containerRef={containerRef} />;
  else if (currentPath === "/prenotazioni") page = <BookingPage containerRef={containerRef} />;
  else if (isPrivacyPage) page = <Privacy />;
  else if (menuPage) page = <MenuDetailPage containerRef={containerRef} page={menuPage} />;

  if (page) {
    return <Suspense fallback={<PageFallback />}>{page}</Suspense>;
  }

  return (
    <div ref={containerRef} className="scroll-container">
      <SiteNav activeSection={activeSection} />

      <main className="main-content">
        <HeroSection />
        <AboutSection />
        <HomeMenuSection />
        <EventsSection />
        <ContactsSection />
      </main>

      <ChatWidget
        isOpen={isChatOpen}
        onOpen={() => setIsChatOpen(true)}
        onClose={closeChat}
      />
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}
