import { lazy, Suspense, useEffect, useState } from "react";

const ChatPanel = lazy(() => import("./ChatPanel"));
const launcherMessages = ["Clicca qui", "Info", "Menu", "Cocktail"];

export default function ChatWidget({ isOpen, onOpen, onClose }) {
  const [launcherIndex, setLauncherIndex] = useState(0);
  const [launcherPaused, setLauncherPaused] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);

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
        type="button"
        className="chat-toggle"
        aria-label="Apri la chat con Nostromo Bot"
        aria-expanded={isOpen}
        aria-controls="ai-chat"
        onClick={handleOpen}
        onMouseEnter={() => setLauncherPaused(true)}
        onMouseLeave={() => setLauncherPaused(false)}
        onFocus={() => setLauncherPaused(true)}
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
        <Suspense fallback={<div id="ai-chat" className="ai-chat-box" aria-live="polite" aria-busy="true" />}>
          <ChatPanel isOpen={isOpen} onClose={onClose} />
        </Suspense>
      )}
    </>
  );
}
