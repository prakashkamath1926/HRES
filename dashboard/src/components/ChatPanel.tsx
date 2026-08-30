/**
 * ChatPanel — HRES Agent Chatbot
 * Floating panel powered by Xkiro LLM, context-aware of live incident state.
 */
import React, { useState, useRef, useEffect, useCallback } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  loading?: boolean;
}

const QUICK_PROMPTS = [
  "What should I do right now?",
  "Where is the nearest hospital?",
  "Where is the nearest fire station?",
  "Is this fire alert real?",
  "How serious is the heat risk?",
  "What are the responder routes?",
];

const PANEL_CSS = `
.chat-fab {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 1000;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  border: none;
  color: #fff;
  font-size: 22px;
  cursor: pointer;
  box-shadow: 0 4px 24px rgba(139,92,246,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
  animation: fab-pulse 3s ease-in-out infinite;
}
.chat-fab:hover { transform: scale(1.1); box-shadow: 0 6px 30px rgba(139,92,246,0.6); }
.chat-fab.has-alert { animation: fab-alert 0.8s ease-in-out infinite; background: linear-gradient(135deg, #ef4444, #f97316); }

@keyframes fab-pulse {
  0%,100% { box-shadow: 0 4px 24px rgba(139,92,246,0.45); }
  50% { box-shadow: 0 4px 32px rgba(139,92,246,0.7); }
}
@keyframes fab-alert {
  0%,100% { box-shadow: 0 4px 24px rgba(239,68,68,0.5); transform: scale(1); }
  50% { box-shadow: 0 4px 36px rgba(239,68,68,0.8); transform: scale(1.05); }
}

.chat-panel {
  position: fixed;
  bottom: 96px;
  right: 28px;
  z-index: 999;
  width: 380px;
  max-height: 560px;
  display: flex;
  flex-direction: column;
  background: #0d1526;
  border: 1px solid rgba(56,89,140,0.5);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(139,92,246,0.15);
  overflow: hidden;
  animation: panel-in 0.25s cubic-bezier(0.34,1.56,0.64,1);
  font-family: 'Inter', sans-serif;
}
@keyframes panel-in {
  from { opacity: 0; transform: scale(0.92) translateY(12px); transform-origin: bottom right; }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.chat-header {
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(59,130,246,0.1));
  border-bottom: 1px solid rgba(56,89,140,0.4);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chat-header-info { display: flex; align-items: center; gap: 10px; }
.chat-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
}
.chat-agent-name { font-size: 13px; font-weight: 600; color: #e8f0fe; }
.chat-agent-sub { font-size: 10px; color: #8ba3cc; letter-spacing: 0.04em; }
.chat-close { background: none; border: none; color: #4d6080; cursor: pointer; font-size: 16px; padding: 4px; border-radius: 4px; }
.chat-close:hover { color: #8ba3cc; background: rgba(255,255,255,0.05); }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 180px;
  max-height: 340px;
  scrollbar-width: thin;
  scrollbar-color: rgba(56,89,140,0.4) transparent;
}

.chat-msg { display: flex; gap: 8px; align-items: flex-start; }
.chat-msg.user { flex-direction: row-reverse; }
.chat-msg-avatar {
  width: 24px; height: 24px;
  border-radius: 50%;
  background: rgba(56,89,140,0.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px;
  flex-shrink: 0;
  margin-top: 2px;
}
.chat-msg.user .chat-msg-avatar {
  background: rgba(139,92,246,0.3);
}
.chat-bubble {
  max-width: 78%;
  padding: 8px 11px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #c8d8f0;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(56,89,140,0.3);
}
.chat-msg.user .chat-bubble {
  background: rgba(139,92,246,0.15);
  border-color: rgba(139,92,246,0.35);
  color: #e8f0fe;
}
.typing-dots span {
  display: inline-block;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #8ba3cc;
  margin: 0 2px;
  animation: blink 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.2; } 40% { opacity: 1; } }

.chat-quick-prompts {
  display: flex;
  gap: 6px;
  padding: 8px 14px;
  overflow-x: auto;
  border-top: 1px solid rgba(56,89,140,0.2);
  scrollbar-width: none;
}
.chat-quick-prompts::-webkit-scrollbar { display: none; }
.quick-btn {
  white-space: nowrap;
  font-size: 10px;
  padding: 4px 9px;
  border-radius: 99px;
  border: 1px solid rgba(56,89,140,0.4);
  background: transparent;
  color: #8ba3cc;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: all 0.15s;
}
.quick-btn:hover { border-color: rgba(139,92,246,0.5); color: #c8a4f8; background: rgba(139,92,246,0.08); }

.chat-input-row {
  display: flex;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid rgba(56,89,140,0.3);
  background: rgba(5,11,20,0.5);
}
.chat-input {
  flex: 1;
  background: rgba(9,18,32,0.9);
  border: 1px solid rgba(56,89,140,0.4);
  border-radius: 8px;
  padding: 8px 11px;
  color: #e8f0fe;
  font-size: 12px;
  font-family: 'Inter', sans-serif;
  outline: none;
  resize: none;
  min-height: 36px;
  max-height: 90px;
  line-height: 1.4;
}
.chat-input:focus { border-color: rgba(139,92,246,0.5); }
.chat-input::placeholder { color: #4d6080; }
.chat-send {
  width: 36px; height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  border: none;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.15s;
}
.chat-send:disabled { opacity: 0.4; cursor: not-allowed; }
.chat-send:hover:not(:disabled) { opacity: 0.85; }
`;

export const ChatPanel: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I'm your HRES Agent 🤖\n\nI have full awareness of the current incident, risk level, weather, and facility routes. Ask me anything — I'm here to help you stay safe.",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const styleRef = useRef<HTMLStyleElement | null>(null);

  // Inject panel CSS
  useEffect(() => {
    if (!styleRef.current) {
      const style = document.createElement("style");
      style.textContent = PANEL_CSS;
      document.head.appendChild(style);
      styleRef.current = style;
    }
    return () => {
      styleRef.current?.remove();
      styleRef.current = null;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(async (text: string) => {
    const userText = text.trim();
    if (!userText || streaming) return;

    const userId = `u-${Date.now()}`;
    const assistantId = `a-${Date.now()}`;

    setMessages(prev => [
      ...prev,
      { id: userId, role: "user", content: userText },
      { id: assistantId, role: "assistant", content: "", loading: true },
    ]);
    setInput("");
    setStreaming(true);

    const history = messages
      .filter(m => !m.loading)
      .map(m => ({ role: m.role, content: m.content }));
    history.push({ role: "user", content: userText });

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history, include_incident_context: true }),
      });

      if (!response.ok) throw new Error(`Chat API error: ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text_chunk = decoder.decode(value, { stream: true });
          const lines = text_chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.content && !data.done) {
                  accumulated += data.content;
                  setMessages(prev =>
                    prev.map(m =>
                      m.id === assistantId
                        ? { ...m, content: accumulated, loading: false }
                        : m
                    )
                  );
                }
              } catch {}
            }
          }
        }
      }
    } catch (err: any) {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, content: `Sorry, I couldn't connect right now. Error: ${err.message}`, loading: false }
            : m
        )
      );
    } finally {
      setStreaming(false);
    }
  }, [messages, streaming]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        className="chat-fab"
        onClick={() => { setOpen(o => !o); setTimeout(() => inputRef.current?.focus(), 100); }}
        title="HRES Agent — Ask me anything"
        aria-label="Open HRES Agent chatbot"
      >
        {open ? "✕" : "🤖"}
      </button>

      {/* Chat Panel */}
      {open && (
        <div className="chat-panel" role="dialog" aria-label="HRES Agent chatbot">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar">🤖</div>
              <div>
                <div className="chat-agent-name">HRES Agent</div>
                <div className="chat-agent-sub">AI · Incident-Aware · Powered by Xkiro</div>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map(msg => (
              <div key={msg.id} className={`chat-msg ${msg.role}`}>
                <div className="chat-msg-avatar">
                  {msg.role === "assistant" ? "🤖" : "👤"}
                </div>
                <div className="chat-bubble">
                  {msg.loading ? (
                    <div className="typing-dots">
                      <span /><span /><span />
                    </div>
                  ) : (
                    msg.content.replace(/\*\*(.*?)\*\*/g, '$1').split("\n").map((line, i) => (
                      <span key={i}>{line}{i < msg.content.replace(/\*\*(.*?)\*\*/g, '$1').split("\n").length - 1 && <br />}</span>
                    ))
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="chat-quick-prompts">
            {QUICK_PROMPTS.map(p => (
              <button
                key={p}
                className="quick-btn"
                onClick={() => sendMessage(p)}
                disabled={streaming}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="chat-input-row">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask HRES Agent anything…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={streaming}
              rows={1}
            />
            <button
              className="chat-send"
              onClick={() => sendMessage(input)}
              disabled={streaming || !input.trim()}
              title="Send"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
};
