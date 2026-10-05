import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Zap } from 'lucide-react';

const SUGGESTED_QUERIES = [
  { label: 'Incident count', template: (zone) => `How many crimes in Zone ${zone}?` },
  { label: 'Safety score', template: (zone) => `What is the safety score of Zone ${zone}?` },
  { label: 'Crime types', template: (zone) => `What crime types are reported in Zone ${zone}?` },
  { label: 'Risk driver', template: (zone) => `What is the risk driver for Zone ${zone}?` },
];

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-slate-700 border border-slate-600 rounded-xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

export default function Chatbot({ token, selectedCity }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'system',
      content: `👋 Hi! I'm your CHASE data assistant. I can answer questions about any zone in **${selectedCity || 'your selected city'}**.\n\nClick a suggestion below or type your own question!`
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [zoneNumber, setZoneNumber] = useState('1');
  const endRef = useRef(null);

  // When city changes, post a context update message
  useEffect(() => {
    setMessages([{
      role: 'system',
      content: `📍 City context switched to **${selectedCity}**. Specify a zone number in your question (e.g., Zone 2, Zone_3) and ask me about:\n- Incident counts\n- Safety / composite scores\n- Top crime types\n- ML risk drivers`
    }]);
  }, [selectedCity]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen, isLoading]);

  const handleSend = async (overrideMsg) => {
    const msgText = overrideMsg || input.trim();
    if (!msgText || isLoading) return;

    const userMsg = { role: 'user', content: msgText };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const r = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msgText, city: selectedCity })
      });
      const data = await r.json();
      setMessages(prev => [...prev, { role: 'system', content: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'system', content: '⚠️ Error reaching the backend. Make sure the server is running on port 8000.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 p-4 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-xl transition-all z-50 ${isOpen ? 'scale-0 opacity-0' : 'scale-100 opacity-100'}`}
      >
        <MessageSquare size={24} />
      </button>

      {/* Chat Panel */}
      <div className={`fixed bottom-6 right-6 w-[420px] h-[580px] bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 z-50 origin-bottom-right ${isOpen ? 'scale-100 opacity-100' : 'scale-90 opacity-0 pointer-events-none'}`}>

        {/* Header */}
        <div className="bg-slate-900/80 backdrop-blur p-4 border-b border-slate-700 flex justify-between items-center flex-shrink-0">
          <div>
            <h3 className="font-bold text-white flex items-center gap-2 text-base">
              <Zap size={18} className="text-blue-400" />
              CHASE Data Assistant
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">City: <span className="text-blue-400 font-medium">{selectedCity}</span> · SQL + ML powered</p>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white transition-colors p-1">
            <X size={20} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-800/50">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-slate-700/80 text-slate-200 rounded-bl-sm border border-slate-600/50'
              }`}>
                {m.content.split('\n').map((line, j) => (
                  <p key={j} className={j > 0 ? 'mt-1' : ''}>
                    {line.replace(/\*\*(.*?)\*\*/g, (_, t) => t)}
                  </p>
                ))}
              </div>
            </div>
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={endRef} />
        </div>

        {/* Quick Suggestions */}
        <div className="px-3 py-2 border-t border-slate-700/50 bg-slate-900/40 flex-shrink-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-slate-500 font-medium">Zone:</span>
            <input
              type="number" min="1" max="20"
              value={zoneNumber}
              onChange={e => setZoneNumber(e.target.value)}
              className="w-14 bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs text-center focus:outline-none focus:border-blue-500 transition-colors"
            />
            <span className="text-xs text-slate-500">→ quick questions:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUERIES.map(q => (
              <button
                key={q.label}
                onClick={() => handleSend(q.template(zoneNumber))}
                disabled={isLoading}
                className="text-xs bg-slate-700 hover:bg-blue-600 border border-slate-600 hover:border-blue-500 rounded-full px-3 py-1 text-slate-300 hover:text-white transition-all disabled:opacity-50"
              >
                {q.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="p-3 bg-slate-900 border-t border-slate-700 flex gap-2 flex-shrink-0">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder={`Ask about ${selectedCity} zones...`}
            disabled={isLoading}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="p-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 text-white rounded-xl transition-colors"
          >
            <Send size={17} />
          </button>
        </div>
      </div>
    </>
  );
}
