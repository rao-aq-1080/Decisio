"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };
type Source = { meeting_id: string; title: string; text: string };

export default function ChatPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [lastSources, setLastSources] = useState<Source[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !token || sending) return;

    const userMessage: Message = { role: "user", content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setSending(true);

    const res = await apiFetch("/chat", token, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: userMessage.content,
        history: messages, // prior turns, not including the message just sent
      }),
    });
    const data = await res.json();

    setMessages([...newMessages, { role: "assistant", content: data.answer }]);
    setLastSources(data.sources || []);
    setSending(false);
  }

  if (loading || !user) return null;

  return (
    <main style={{ maxWidth: 800, margin: "0 auto", padding: "48px 20px", display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <div style={{ marginBottom: 16 }}>
        <Link href="/dashboard" style={{ color: "#2f81f7" }}>&larr; Back to dashboard</Link>
      </div>
      <h1>💬 Chat with your meetings</h1>
      <p style={{ color: "#8b949e" }}>
        Ask anything across all your meetings — follow-up questions work too.
      </p>

      <div style={{ flex: 1, overflowY: "auto", marginBottom: 16 }}>
        {messages.length === 0 && (
          <p style={{ color: "#8b949e" }}>
            Try: "What decisions did we make last week?" or "Who owns the onboarding wizard?"
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...bubble,
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "#2f81f7" : "#151b23",
              marginLeft: m.role === "user" ? "auto" : 0,
              marginRight: m.role === "user" ? 0 : "auto",
            }}
          >
            {m.content}
          </div>
        ))}
        {sending && <div style={{ ...bubble, background: "#151b23" }}>Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      {lastSources.length > 0 && (
        <div style={{ marginBottom: 16, fontSize: 13, color: "#8b949e" }}>
          <b>Sources:</b>{" "}
          {lastSources.map((s, i) => (
            <Link key={i} href={`/meeting/${s.meeting_id}`} style={{ color: "#2f81f7", marginRight: 8 }}>
              {s.title}
            </Link>
          ))}
        </div>
      )}

      <form onSubmit={handleSend} style={{ display: "flex", gap: 8 }}>
        <input
          type="text" placeholder="Ask about your meetings..." value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ flex: 1, padding: 12, borderRadius: 6, border: "1px solid #2a333d", background: "#151b23", color: "#e6edf3" }}
        />
        <button type="submit" disabled={!input.trim() || sending} style={buttonStyle}>
          Send
        </button>
      </form>
    </main>
  );
}

const bubble: React.CSSProperties = {
  maxWidth: "75%",
  padding: "10px 14px",
  borderRadius: 10,
  marginBottom: 10,
  whiteSpace: "pre-wrap",
  display: "block",
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 18px", borderRadius: 6, border: "none",
  background: "#2f81f7", color: "white", cursor: "pointer",
};
