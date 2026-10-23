import { Component, lazy, Suspense, useEffect, useRef, useState } from "react";
import { contactInfo } from "../data/contactInfo.js";

const loadChatPanel = () => import("./ChatPanel");
const ChatPanel = lazy(loadChatPanel);
const launcherMessages = ["Clicca qui", "Info", "Menu", "Cocktail"];

class ChatBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (!this.state.failed) return this.props.children;
    return this.props.isOpen && <div id="ai-chat" className="ai-chat-box" role="dialog" aria-label="Nostromo non disponibile">
      <div className="chat-header">Nostromo<button type="button" className="close-chat" aria-label="Chiudi la chat" onClick={this.props.onClose}>×</button></div>
      <div className="chat-messages"><p className="message bot" role="alert">Rotta interrotta, Capitano. Ricarica la pagina per riaprire la chat, oppure <a className="chat-link" href="/prenota">apri il modulo prenotazioni</a> o <a className="chat-link" href={contactInfo.phoneHref}>chiama la ciurma</a>.</p></div>
    </div>;
  }
}

export default function ChatWidget({ isOpen, onOpen, onClose }) {
  const [launcherIndex, setLauncherIndex] = useState(0);
  const [launcherPaused, setLauncherPaused] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);
  const launcherRef = useRef(null);
  const previousOpenRef = useRef(isOpen);

  useEffect(() => {
    if (!isOpen && previousOpenRef.current) launcherRef.current?.focus({ preventScroll: true });
    previousOpenRef.current = isOpen;
  }, [isOpen]);

  function preloadChat() { loadChatPanel().catch(() => {}); }

  function handleOpen() {
    setHasOpened(true);
    onOpen();
  }

  useEffect(() => {
    if (isOpen || launcherPaused) return undefined;
    const timer = window.setInterval(() => {
      setLauncherIndex((current) => (current + 1) % launcherMessages.length);
    }, 15000);
    return () => window.clearInterval(timer);
  }, [isOpen, launcherPaused]);

  return (
    <>
      <button
        ref={launcherRef}
        type="button"
        className="chat-toggle"
        aria-label="Apri la chat con Nostromo Bot"
        aria-expanded={isOpen}
        aria-controls="ai-chat"
        onClick={handleOpen}
        onPointerDown={preloadChat}
        onMouseEnter={() => { setLauncherPaused(true); preloadChat(); }}
        onMouseLeave={() => setLauncherPaused(false)}
        onFocus={() => { setLauncherPaused(true); preloadChat(); }}
        onBlur={() => setLauncherPaused(false)}
      >
        <img
          src={`${import.meta.env.BASE_URL}images/logo/pirate-ship-assistant.webp`}
          alt=""
          aria-hidden="true"
          width="164"
          height="164"
        />
        {!isOpen && <span className="chat-tooltip" aria-hidden="true">{launcherMessages[launcherIndex]}</span>}
      </button>

      {hasOpened && (
        <ChatBoundary isOpen={isOpen} onClose={onClose}>
          <Suspense fallback={isOpen ? <div id="ai-chat" className="ai-chat-box" role="status" aria-busy="true"><div className="chat-header">Apro la rotta con Nostromo…<button type="button" className="close-chat" aria-label="Chiudi la chat" onClick={onClose}>×</button></div></div> : null}>
            <ChatPanel isOpen={isOpen} onClose={onClose} />
          </Suspense>
        </ChatBoundary>
      )}
    </>
  );
}
