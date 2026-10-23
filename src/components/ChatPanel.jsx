import { useEffect, useRef, useState } from "react";
import { BOOKING_PATH, classifyQuestion, errorMessage, quickQuestionGroups, quickQuestions, requestReply, welcomeMessage } from "../utils/nostromo.js";
import { contactInfo } from "../data/contactInfo.js";

const linkPattern = /(\+?39\s?339\s?751\s?4140|339\s?751\s?4140|\/prenotazioni\/gestisci|\/prenotazioni|\/prenota|\/privacy|\/menu-food|\/menu-drink|\/#contatti)(?![\w/-])/g;
const linkLabels = { "/prenota": "Apri il modulo prenotazioni", "/prenotazioni": "Apri il modulo prenotazioni", "/prenotazioni/gestisci": "Gestisci la prenotazione", "/privacy": "Informativa privacy", "/menu-food": "Menu Food", "/menu-drink": "Menu Drink", "/#contatti": "Mappa e contatti" };

function renderMessage(text, sender) {
  if (sender !== "bot") return text;
  return text.split(linkPattern).map((part, index) => {
    if (linkLabels[part]) return <a key={index} className="chat-link" href={part === "/prenotazioni" ? BOOKING_PATH : part}>{linkLabels[part]}</a>;
    if (/^(?:\+?39\s?)?339\s?751\s?4140$/.test(part)) return <a key={index} href={contactInfo.phoneHref} className="chat-phone-link">{part}</a>;
    return part;
  });
}

export default function ChatPanel({ isOpen, onClose }) {
  const [messages, setMessages] = useState([{ id: "welcome", sender: "bot", text: welcomeMessage }]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [questionIndexes, setQuestionIndexes] = useState([0, 0, 0, 0]);
  const [contextualQuestions, setContextualQuestions] = useState({});
  const [failedMessage, setFailedMessage] = useState(null);
  const [retryAt, setRetryAt] = useState(0);
  const [retryScope, setRetryScope] = useState("chat");
  const [now, setNow] = useState(Date.now);
  const messageListRef = useRef(null);
  const panelRef = useRef(null);
  const closeRef = useRef(null);
  const sessionTokenRef = useRef(null);
  const [context, setContext] = useState({});
  const sendingRef = useRef(false);
  const controllerRef = useRef(null);
  const pendingTextRef = useRef(null);
  const followMessagesRef = useRef(true);
  const waitingSeconds = Math.max(0, Math.ceil((retryAt - now) / 1000));
  const requestScope = text => {
    const topic = classifyQuestion(text, context).topic;
    return ["menu", "food", "drink", "analcolici"].includes(topic) ? "menu" : topic === "chat" ? "chat" : null;
  };
  const needsCooldown = text => waitingSeconds > 0 && requestScope(text) === retryScope;
  const visibleQuestions = quickQuestionGroups.map((group, slot) => {
    const options = [...group.questions, ...(contextualQuestions[slot] ?? [])];
    return { ...group, slot, text: options[questionIndexes[slot] % options.length] };
  });

  useEffect(() => () => controllerRef.current?.abort(), []);
  useEffect(() => {
    const viewport = window.visualViewport;
    if (!isOpen || !viewport) return undefined;
    const resize = () => {
      panelRef.current?.style.setProperty("--chat-viewport-height", `${viewport.height}px`);
      panelRef.current?.style.setProperty("--chat-bottom-offset", `${Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop)}px`);
    };
    resize();
    viewport.addEventListener("resize", resize);
    viewport.addEventListener("scroll", resize);
    return () => { viewport.removeEventListener("resize", resize); viewport.removeEventListener("scroll", resize); };
  }, [isOpen]);
  useEffect(() => {
    if (!isOpen) return undefined;
    closeRef.current?.focus({ preventScroll: true });
    const closeOnEscape = event => {
      if (event.key === "Escape") { event.preventDefault(); onClose(); }
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isOpen, onClose]);
  useEffect(() => {
    if (!isOpen || !followMessagesRef.current) return;
    const list = messageListRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [isOpen, messages, isLoading]);
  useEffect(() => {
    if (!retryAt) return undefined;
    const timer = window.setInterval(() => {
      const time = Date.now();
      setNow(time);
      if (time >= retryAt) setRetryAt(0);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [retryAt]);
  useEffect(() => {
    if (!isOpen) return undefined;
    const timer = window.setInterval(() => {
      setQuestionIndexes(current => current.map((index, slot) => (index + 1) % (quickQuestionGroups[slot].questions.length + (contextualQuestions[slot]?.length ?? 0))));
    }, 12000);
    return () => window.clearInterval(timer);
  }, [isOpen, contextualQuestions]);

  async function sendMessage(text, retry = false) {
    const cleanText = text.trim();
    if (!cleanText || sendingRef.current || Date.now() < retryAt && requestScope(cleanText) === retryScope) return;
    sendingRef.current = true;
    followMessagesRef.current = true;
    if (!retry) {
      setMessages(current => [...current, { id: crypto.randomUUID(), sender: "user", text: cleanText }]);
      setInput("");
    }
    setFailedMessage(null);
    setIsLoading(true);
    const controller = new AbortController();
    controllerRef.current = controller;
    pendingTextRef.current = cleanText;
    try {
      const data = await requestReply(cleanText, { sessionToken: sessionTokenRef.current, context, signal: controller.signal });
      if (controller.signal.aborted) return;
      sessionTokenRef.current = data.sessionToken;
      setContext(data.context);
      const topic = data.context?.topic;
      const slot = topic === "food" ? 0 : ["drink", "analcolici"].includes(topic) ? 1 : /compleann|event|festa|apericena|pacchett/i.test(cleanText) ? 3 : 2;
      const contextual = data.quickReplies.filter(question => !quickQuestions.includes(question)).slice(0, 4);
      setContextualQuestions(current => ({ ...current, [slot]: contextual }));
      if (contextual.length) setQuestionIndexes(current => current.map((index, itemSlot) => itemSlot === slot ? quickQuestionGroups[slot].questions.length : index));
      setMessages(current => [...current, { id: crypto.randomUUID(), sender: "bot", text: data.reply }]);
    } catch (error) {
      if (controller.signal.aborted) return;
      setMessages(current => [...current, { id: crypto.randomUUID(), sender: "bot", text: errorMessage(error) }]);
      setFailedMessage(cleanText);
      if (error.code === "rate-limit") {
        const time = Date.now();
        setNow(time);
        setRetryAt(time + Math.max(1, error.retryAfter) * 1000);
        setRetryScope(error.scope);
      }
    } finally {
      if (!controller.signal.aborted) {
        sendingRef.current = false;
        setIsLoading(false);
        pendingTextRef.current = null;
      }
    }
  }

  function resetTopic() {
    sessionTokenRef.current = null;
    setContext({});
    setContextualQuestions({});
    setQuestionIndexes([0, 0, 0, 0]);
    setFailedMessage(null);
    followMessagesRef.current = true;
    setMessages(current => [...current, { id: crypto.randomUUID(), sender: "bot", text: "Nuova rotta, Capitano! Chiedimi del locale, dei piatti, dei cocktail o degli eventi. Per prenotare apri /prenota." }]);
  }

  if (!isOpen) return null;

  return (
    <div ref={panelRef} id="ai-chat" className="ai-chat-box" role="dialog" aria-labelledby="nostromo-title">
      <div className="chat-header"><span id="nostromo-title">Nostromo · La guida del Makai</span><button ref={closeRef} type="button" className="close-chat" aria-label="Chiudi la chat" onClick={onClose}>×</button></div>
      <nav className="chat-actions" aria-label="Collegamenti rapidi Makai">
        <a href="/menu-food">Food</a><a href="/menu-drink">Drink</a>
        <a href={contactInfo.phoneHref}>Chiama</a><a href={BOOKING_PATH}>Prenota</a>
      </nav>
      <div ref={messageListRef} className="chat-messages" role="log" aria-label="Conversazione con Nostromo" aria-live="polite" aria-relevant="additions" onScroll={() => {
        const list = messageListRef.current;
        followMessagesRef.current = list.scrollHeight - list.scrollTop - list.clientHeight < 60;
      }}>
        {messages.map(message => <div key={message.id} className={`message ${message.sender}`}>{renderMessage(message.text, message.sender)}</div>)}
        {isLoading && <div className="message bot chat-loading" role="status">Consulto i registri di bordo…</div>}
      </div>
      {isLoading && <button className="chat-retry" type="button" onClick={() => {
        controllerRef.current?.abort();
        sendingRef.current = false;
        setIsLoading(false);
        setFailedMessage(pendingTextRef.current);
        pendingTextRef.current = null;
        setMessages(current => [...current, { id: crypto.randomUUID(), sender: "bot", text: "Ricerca interrotta, Capitano. Puoi riprovare la domanda oppure scegliere una nuova rotta." }]);
      }}>Interrompi l’attesa</button>}
      {failedMessage && <button type="button" className="chat-retry" onClick={() => sendMessage(failedMessage, true)} disabled={isLoading || needsCooldown(failedMessage)}>{needsCooldown(failedMessage) ? `Riprova tra ${waitingSeconds}s` : "Riprova l’ultima domanda"}</button>}
      <div className="chat-quick-questions" aria-label="Domande suggerite">
        {visibleQuestions.map(({ id, slot, text }) => <button key={id} type="button" onClick={() => {
          const group = quickQuestionGroups[slot];
          sendMessage(text);
          setQuestionIndexes(current => current.map((index, itemSlot) => itemSlot === slot ? (index + 1) % (group.questions.length + (contextualQuestions[slot]?.length ?? 0)) : index));
        }} disabled={isLoading || needsCooldown(text)}>{text}</button>)}
      </div>
      <button className="chat-topic-reset" type="button" onClick={resetTopic} disabled={isLoading}>Cambia argomento</button>
      <form className="chat-input-area" onSubmit={event => { event.preventDefault(); sendMessage(input); }}>
        <input type="text" value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && event.nativeEvent.isComposing) event.preventDefault(); }} placeholder="Chiedi a Nostromo…" maxLength={500} aria-label="Scrivi un messaggio" autoComplete="off" enterKeyHint="send" />
        <button className="send-btn" type="submit" disabled={isLoading || needsCooldown(input) || !input.trim()} aria-label="Invia messaggio">➤</button>
      </form>
    </div>
  );
}
