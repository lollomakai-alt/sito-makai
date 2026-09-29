import { useEffect, useRef, useState } from "react";

const welcomeMessages = [
  "Arrr, benvenuto a bordo. Sono la vedetta digitale del Makai: quale rotta scegli?",
  "Ahoy, Capitano! La ciurma è pronta. Chiedimi di menu, cocktail, eventi o prenotazioni.",
  "Benvenuto sulla nave del Makai. Dimmi la destinazione e tracciamo la rotta.",
  "Il timone è tuo, pirata. Posso guidarti tra informazioni sul locale, menu ed eventi.",
  "Ciurma pronta, cannoni spenti, chatbot acceso. Che si combina?",
];

const thinkingMessages = [
  "Consulto le mappe, Capitano…",
  "Un momento, sto tracciando la rotta…",
  "Sto cercando tra i registri di bordo…",
  "La ciurma sta controllando…",
  "Interrogo il pappagallo digitale…",
];

const errorMessages = [
  "Arrr… abbiamo urtato uno scoglio.",
  "Tempesta improvvisa sulla rotta.",
  "La bussola è impazzita.",
  "C'è stato un piccolo ammutinamento tecnico.",
];

function randomMessage(messages) {
  return messages[Math.floor(Math.random() * messages.length)];
}

function createInitialMessage() {
  return {
    id: "welcome",
    sender: "bot",
    text: randomMessage(welcomeMessages),
  };
}

const quickQuestionGroups = [
  {
    id: "menu",
    questions: [
      "Mi consigli un piatto di carne?",
      "Mi consigli un piatto di pesce?",
      "Quali piatti vegetariani avete?",
      "Cosa posso mangiare senza pollo?",
    ],
  },
  {
    id: "cocktail",
    questions: [
      "Mi consigli un cocktail?",
      "Mi consigli un cocktail con rum?",
      "Quale analcolico mi consigli?",
      "Mi consigli un drink della ciurma?",
    ],
  },
  {
    id: "locale",
    questions: [
      "Come arrivo con la Metro C?",
      "Ci sono parcheggi vicini?",
      "Quali sono gli orari?",
      "Quanto si spende mediamente per cena?",
    ],
  },
  {
    id: "eventi",
    questions: [
      "Vorrei prenotare un tavolo.",
      "Posso organizzare un compleanno?",
      "Quali pacchetti festa proponete?",
      "Fate apericena per gli eventi?",
    ],
  },
];

function pickQuestionIndex(questionCount, previousIndex = -1) {
  const randomIndex = Math.floor(Math.random() * questionCount);
  if (questionCount > 1 && randomIndex === previousIndex) {
    return (randomIndex + 1) % questionCount;
  }
  return randomIndex;
}

function createQuickQuestions(previousQuestions = []) {
  return quickQuestionGroups.map((group) => {
    const previous = previousQuestions.find((question) => question.groupId === group.id);
    const questionIndex = pickQuestionIndex(group.questions.length, previous?.questionIndex);
    return {
      groupId: group.id,
      questionIndex,
      text: group.questions[questionIndex],
    };
  });
}

const phonePattern = /(\+39\s?339\s?751\s?4140|339\s?751\s?4140|\+393397514140)/g;
const singlePhonePattern = /^(\+39\s?339\s?751\s?4140|339\s?751\s?4140|\+393397514140)$/;

function renderMessage(text, sender) {
  if (sender !== "bot") return text;
  return text.split(phonePattern).map((part, index) => {
    if (!part || !singlePhonePattern.test(part)) return part;
    const phone = part.replace(/\s/g, "");
    return <a key={`${part}-${index}`} href={`tel:${phone}`} className="chat-phone-link">{part}</a>;
  });
}

export default function ChatWidget({ isOpen, onOpen, onClose }) {
  const [messages, setMessages] = useState(() => [createInitialMessage()]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState(thinkingMessages[0]);
  const [quickQuestions, setQuickQuestions] = useState(() => createQuickQuestions());
  const messagesEndRef = useRef(null);
  const sessionTokenRef = useRef(null);
  const sendingRef = useRef(false);
  const wasOpenRef = useRef(isOpen);

  useEffect(() => {
    if (isOpen && !wasOpenRef.current) {
      setQuickQuestions((current) => createQuickQuestions(current));
    }
    wasOpenRef.current = isOpen;
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [isOpen, messages, isLoading]);

  async function sendMessage(text) {
    const cleanText = text.trim();
    if (!cleanText || sendingRef.current) return;
    sendingRef.current = true;

    const userMessage = { id: crypto.randomUUID(), sender: "user", text: cleanText };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setLoadingMessage(randomMessage(thinkingMessages));
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: cleanText,
          session_token: sessionTokenRef.current,
        }),
      });

      if (!response.ok) throw new Error(`Chat API: ${response.status}`);
      const data = await response.json();
      if (typeof data.reply !== "string") throw new Error("Risposta chat non valida");
      sessionTokenRef.current = data.session_token ?? null;

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
          text: `${randomMessage(errorMessages)} Riprova tra poco o contattaci al 339 751 4140.`,
        },
      ]);
    } finally {
      sendingRef.current = false;
      setIsLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage(input);
  }

  function handleQuickQuestion(selectedQuestion) {
    if (sendingRef.current) return;
    const group = quickQuestionGroups.find(({ id }) => id === selectedQuestion.groupId);
    if (!group) return;

    sendMessage(selectedQuestion.text);
    setQuickQuestions((current) => current.map((question) => {
      if (question.groupId !== selectedQuestion.groupId) return question;
      const questionIndex = (question.questionIndex + 1) % group.questions.length;
      return {
        ...question,
        questionIndex,
        text: group.questions[questionIndex],
      };
    }));
  }

  return (
    <>
      <button
        type="button"
        className="chat-toggle"
        aria-label="Apri la chat con Nostromo Bot"
        aria-expanded={isOpen}
        aria-controls="ai-chat"
        onClick={onOpen}
      >
        <img
          src={`${import.meta.env.BASE_URL}images/logo/pirate-ship-assistant.png`}
          alt=""
          aria-hidden="true"
        />
        <span className="chat-tooltip">Ehi, pirata! Chiedimi tutto!</span>
      </button>

      {isOpen && (
        <div id="ai-chat" className="ai-chat-box">
          <div className="chat-header">
            <span>Nostromo Bot</span>
            <button className="close-chat" onClick={onClose}>×</button>
          </div>
          <div className="chat-messages" aria-live="polite">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}`}>
                {renderMessage(message.text, message.sender)}
              </div>
            ))}
            {isLoading && <div className="message bot chat-loading">{loadingMessage}</div>}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-quick-questions">
            {quickQuestions.map((question) => (
              <button key={question.groupId} type="button" onClick={() => handleQuickQuestion(question)} disabled={isLoading}>
                {question.text}
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
