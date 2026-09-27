import { useEffect, useRef, useState } from "react";

const initialMessage = {
  id: "welcome",
  sender: "bot",
  text: "Aloha! Posso aiutarti con menu, cocktail, contatti, eventi e prenotazioni.",
};

const quickQuestions = [
  "Cosa posso mangiare?",
  "Quali cocktail avete?",
  "Come posso prenotare?",
  "Dove si trova il Makai?",
];

export default function ChatWidget({ isOpen, onOpen, onClose }) {
  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (isOpen) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [isOpen, messages, isLoading]);

  async function sendMessage(text) {
    const cleanText = text.trim();
    if (!cleanText || isLoading) return;

    const userMessage = { id: crypto.randomUUID(), sender: "user", text: cleanText };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: cleanText,
          history: messages.slice(-10),
        }),
      });

      if (!response.ok) throw new Error(`Chat API: ${response.status}`);
      const data = await response.json();
      if (typeof data.reply !== "string") throw new Error("Risposta chat non valida");

      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), sender: "bot", text: data.reply },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          sender: "bot",
          text: "La rotta è momentaneamente interrotta. Riprova tra poco o contattaci al 339 751 4140.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage(input);
  }

  return (
    <>
      <button
        type="button"
        className="chat-toggle"
        aria-label="Apri la chat con il Capitano Makai"
        aria-expanded={isOpen}
        aria-controls="ai-chat"
        onClick={onOpen}
      >
        <img
          src={`${import.meta.env.BASE_URL}images/pirate-ship-assistant.png`}
          alt=""
          aria-hidden="true"
        />
        <span className="chat-tooltip">Ehi, pirata! Chiedimi tutto!</span>
      </button>

      {isOpen && (
        <div id="ai-chat" className="ai-chat-box">
          <div className="chat-header">
            <span>AI Concierge Makai</span>
            <button className="close-chat" onClick={onClose}>×</button>
          </div>
          <div className="chat-messages" aria-live="polite">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}`}>
                {message.text}
              </div>
            ))}
            {isLoading && <div className="message bot chat-loading">Sto consultando la mappa…</div>}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-quick-questions">
            {quickQuestions.map((question) => (
              <button key={question} type="button" onClick={() => sendMessage(question)} disabled={isLoading}>
                {question}
              </button>
            ))}
          </div>
          <form className="chat-input-area" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Chiedi al capitano..."
              maxLength="500"
              disabled={isLoading}
              aria-label="Scrivi un messaggio"
            />
            <button className="send-btn" type="submit" disabled={isLoading || !input.trim()} aria-label="Invia messaggio">➤</button>
          </form>
        </div>
      )}
    </>
  );
}
