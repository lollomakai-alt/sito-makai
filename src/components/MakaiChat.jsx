import React, { useState, useRef, useEffect } from 'react';

export default function MakaiChat({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Aloha! 🌺 Benvenuto al Makai Grand Line. Sono il tuo navigatore IA. Cosa posso fare per te oggi?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Domande reimpostate e usabili (Quick Prompts)
  const quickQuestions = [
      "Vorrei prenotare un tavolo.",
      "Cosa mi consigli dal menu?",
      "Avete pacchetti per feste o eventi?",
      "Posso organizzare un compleanno da voi?"
  ];

  // Scroll automatico in basso quando arriva un messaggio
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;

    const userMsg = text;
    setInput(''); // Pulisce l'input
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Ops, la Rotta Maggiore è interrotta! Riprova più tardi.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = (question) => {
    sendMessage(question);
  };

  // Se la chat non è aperta, non renderizzare nulla
  if (!isOpen) return null;

  return (
    // Overlay scuro di sfondo
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-end justify-center md:items-center md:justify-end p-0 md:p-6 animate-fadeIn">
      
      {/* Finestra della Chat (Mobile: a tutto schermo in basso, Desktop: pannello) */}
      <div className="w-full h-[80vh] md:h-[600px] md:w-[400px] bg-stone-950 rounded-t-3xl md:rounded-2xl shadow-2xl border border-amber-800 flex flex-col overflow-hidden animate-slideUp">
        
        {/* Header Chat */}
        <div className="bg-stone-900 p-4 flex items-center justify-between border-b border-amber-900/50 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div> {/* Indicatore Online */}
            <span className="text-3xl">🗿</span>
            <div>
              <h3 className="font-bold text-white tracking-wide">Nostromo Bot</h3>
              <p className="text-xs text-green-300">Online - Esperto di One Piece</p>
            </div>
          </div>
          <button onClick={onClose} className="text-stone-500 hover:text-white p-2 rounded-full hover:bg-stone-800 transition">
            ✕
          </button>
        </div>

        {/* Area Messaggi */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-stone-950/50">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-stone-800 flex items-center justify-center text-lg shrink-0 mt-1">🗿</div>
              )}
              <div className={`p-4 rounded-2xl max-w-[85%] shadow ${m.role === 'user' ? 'bg-amber-600 text-stone-950 rounded-br-none' : 'bg-stone-900 text-amber-50 rounded-bl-none border border-amber-900/30'}`}>
                <p className="text-sm leading-relaxed">{m.content}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-stone-800 flex items-center justify-center text-lg shrink-0">🗿</div>
              <div className="p-4 rounded-2xl bg-stone-900 text-amber-50 rounded-bl-none border border-amber-900/30">
                <div className="flex gap-1.5 items-center h-5">
                    <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* SEZIONE DOMANDE REIMPOSTATE (Usabilità immediata) */}
        <div className="bg-stone-900 p-4 border-t border-amber-900/50 shrink-0">
          <p className="text-xs text-amber-600 mb-2.5 px-1">💡 Chiedi rapidamente:</p>
          <div className="grid grid-cols-2 gap-2">
            {quickQuestions.map((question, index) => (
              <button 
                key={index}
                onClick={() => handleQuickQuestion(question)}
                disabled={loading}
                className="text-left bg-stone-800 text-amber-100 text-xs p-3 rounded-lg hover:bg-amber-900/70 hover:text-white transition disabled:opacity-50 border border-amber-700/30"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }} className="bg-stone-950 p-4 flex gap-3 border-t border-amber-900/50 shrink-0">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Scrivi la tua domanda da pirata..."
            className="flex-1 bg-stone-900 border border-amber-900/50 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition"
            disabled={loading}
          />
          <button 
            type="submit" 
            disabled={loading || !input.trim()}
            className="bg-amber-500 text-stone-950 px-6 py-3 rounded-xl font-bold text-sm hover:bg-white transition disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? '...' : 'Invia'} 🚀
          </button>
        </form>
      </div>

    </div>
  );
}