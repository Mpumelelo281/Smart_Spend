import { useEffect, useRef, useState } from "react";

import { api } from "../api/client.js";
import { IconChat, IconSend, IconX } from "./icons.jsx";

// Not persisted anywhere (no backend chat-history table, no localStorage) —
// SpendWise is stateless by design (see backend/apps/assistant/engine.py):
// every reply is recomputed fresh from the student's current data, so there
// is nothing meaningful to resume across a reload. Closing the panel (or
// refreshing) just starts a new conversation.
const GREETING_TRIGGER = "Hi";

let nextId = 0;
function newId() {
  nextId += 1;
  return nextId;
}

function Bubble({ role, text }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <p
        className={`max-w-[85%] whitespace-pre-line rounded-2xl px-3.5 py-2 text-sm ${
          isUser
            ? "rounded-br-sm bg-brand-600 text-white"
            : "rounded-bl-sm bg-slate-100 text-slate-700 dark:bg-navy-800 dark:text-slate-200"
        }`}
      >
        {text}
      </p>
    </div>
  );
}

export default function AssistantChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [quickReplies, setQuickReplies] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sending]);

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    setMessages((prev) => [...prev, { id: newId(), role: "user", text: trimmed }]);
    setQuickReplies([]);
    setInput("");
    setSending(true);
    try {
      const { data } = await api.post("/assistant/ask/", { message: trimmed });
      setMessages((prev) => [...prev, { id: newId(), role: "bot", text: data.reply }]);
      setQuickReplies(data.quick_replies || []);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "bot",
          text: "Sorry, I couldn't reach the server just now. Please try again in a moment.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  function handleOpen() {
    setOpen(true);
    if (!startedRef.current) {
      startedRef.current = true;
      send(GREETING_TRIGGER);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 sm:bottom-6 sm:right-6">
      {open && (
        <div className="mb-3 flex h-[28rem] w-[calc(100vw-2rem)] max-w-sm flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card dark:border-navy-700 dark:bg-navy-900">
          <div className="flex items-center justify-between border-b border-slate-100 bg-brand-600 px-4 py-3 text-white dark:border-navy-800">
            <div>
              <p className="text-sm font-semibold">SpendWise 🤖</p>
              <p className="text-xs text-brand-100">Budgeting help, not financial advice.</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="flex h-7 w-7 items-center justify-center rounded-full text-brand-100 transition-colors hover:bg-white/10 hover:text-white"
            >
              <IconX className="h-4 w-4" />
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {messages.map((m) => (
              <Bubble key={m.id} role={m.role} text={m.text} />
            ))}
            {sending && (
              <div className="flex justify-start">
                <p className="rounded-2xl rounded-bl-sm bg-slate-100 px-3.5 py-2 text-sm text-slate-400 dark:bg-navy-800 dark:text-slate-500">
                  Typing…
                </p>
              </div>
            )}
          </div>

          {quickReplies.length > 0 && !sending && (
            <div className="flex flex-wrap gap-2 border-t border-slate-100 px-4 py-3 dark:border-navy-800">
              {quickReplies.map((q) => (
                <button
                  key={q.label}
                  onClick={() => send(q.message)}
                  className="rounded-full border border-brand-200 px-3 py-1.5 text-xs font-medium text-brand-700 transition-colors hover:bg-brand-50 dark:border-brand-700/50 dark:text-brand-300 dark:hover:bg-navy-800"
                >
                  {q.label}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-slate-100 p-3 dark:border-navy-800">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your spending…"
              disabled={sending}
              className="flex-1 rounded-full border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm text-slate-900 outline-none focus:border-brand-400 disabled:opacity-60 dark:border-navy-700 dark:bg-navy-800 dark:text-white"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              aria-label="Send"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
            >
              <IconSend className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => (open ? setOpen(false) : handleOpen())}
        aria-label={open ? "Close SpendWise assistant" : "Open SpendWise assistant"}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-white shadow-card transition-colors hover:bg-brand-700"
      >
        {open ? <IconX className="h-6 w-6" /> : <IconChat className="h-6 w-6" />}
      </button>
    </div>
  );
}
