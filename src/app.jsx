import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import "./styles/app.css";
import "./styles/hero.css";
import "./styles/chi-siamo.css";
import "./styles/menu.css";
import "./styles/eventi.css";
import "./styles/galleria.css";
import "./styles/contatti.css";
import "./styles/chat.css";

import AboutSection from "./components/AboutSection";
import ChatWidget from "./components/ChatWidget";
import ContactsSection from "./components/ContactsSection";
import EventsSection from "./components/EventsSection";
import HeroSection from "./components/HeroSection";
import HomeMenuSection from "./components/HomeMenuSection";
import SiteNav from "./components/SiteNav";
import { menuPages } from "./data/siteContent";
import GalleryPage from "./pages/GalleryPage";
import MenuDetailPage from "./pages/MenuDetailPage";

gsap.registerPlugin(ScrollTrigger);

function App() {
  const containerRef = useRef(null);
  const [activeSection] = useState("Chi siamo");
  const [isChatOpen, setIsChatOpen] = useState(false);

  const currentPath = window.location.pathname.replace(/\/$/, "") || "/";
  const menuPage = menuPages[currentPath];
  const isGalleryPage = currentPath === "/galleria";

  useEffect(() => {
    if (!containerRef.current) return undefined;

    const ctx = gsap.context(() => {
      gsap.set(containerRef.current, {
        backgroundImage: `url(${import.meta.env.BASE_URL}images/Tramonto.png)`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
      });

      if (currentPath !== "/") return;

        gsap.fromTo(
          ".hero-main-img",
          {
            y: 30,
            opacity: 0,
          },
          {
            y: 0,
            opacity: 1,
            ease: "none",
            scrollTrigger: {
              trigger: ".hero-section",
              start: "top top",
              end: "+=30%",
              scrub: 0.8,
            },
          }
        );

        gsap.fromTo(
          ".about-photos img:first-child",
          { x: -30, opacity: 0 },
          {
            x: 0,
            opacity: 1,
            ease: "none",
            scrollTrigger: {
              trigger: ".about-section",
              start: "top 98%",
              end: "top 18%",
              scrub: 1.4,
            },
          }
        );

        gsap.fromTo(
          ".about-photos img:last-child",
          { x: 30, opacity: 0 },
          {
            x: 0,
            opacity: 1,
            ease: "none",
            scrollTrigger: {
              trigger: ".about-section",
              start: "top 98%",
              end: "top 18%",
              scrub: 1.4,
            },
          }
        );

        gsap.fromTo(
          [".about-subtitle", ".about-description"],
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            ease: "none",
            scrollTrigger: {
              trigger: ".about-subtitle",
              start: "top 98%",
              end: "top 30%",
              scrub: 1.4,
            },
          }
        );

        const reveals = [
          [".about-section", [".about-title"]],
          [".events-section", [".events-title", ".events-copy", ".events-gallery-panel"]],
          [".contacts-section", [".contacts-title", ".contacts-totem", ".contacts-content"]],
        ];

        reveals.forEach(([trigger, targets]) => {
          const elements = targets.flatMap((selector) =>
            gsap.utils.toArray(selector, containerRef.current)
          );

          gsap.from(elements, {
            y: 120,
            opacity: 0,
            scale: 0.12,
            stagger: 0.08,
            ease: "none",
            scrollTrigger: {
              trigger,
              start: "top 98%",
              end: "top 18%",
              scrub: 1.4,
            },
          });
        });

        requestAnimationFrame(() => ScrollTrigger.refresh());

    }, containerRef);

    return () => ctx.revert();
  }, [currentPath]);

  if (isGalleryPage) {
    return <GalleryPage containerRef={containerRef} />;
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
        <ContactsSection onOpenChat={() => setIsChatOpen(true)} />
      </main>

      <ChatWidget
        isOpen={isChatOpen}
        onOpen={() => setIsChatOpen(true)}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}

export default App;
