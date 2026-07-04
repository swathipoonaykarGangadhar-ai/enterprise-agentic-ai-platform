import { useState, useRef } from "react";

const API_BASE = "http://localhost:8000";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const isSendingRef = useRef(false);

  async function handleSend() {
    if (!input.trim() || isSendingRef.current) return;
    isSendingRef.current = true;
    const question = input;
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setStreaming(true);

    // Add an empty assistant message we'll fill in as chunks arrive
    setMessages((prev) => [...prev, { role: "assistant", text: "" }]);

    try {
      const res = await fetch(`${API_BASE}/ask-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // keep incomplete chunk for next read

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = JSON.parse(line.slice(6));
          if (payload.chunk) {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = { ...last, text: last.text + payload.chunk };
              return updated;
            });
          }
        }
      }
    } catch (e) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].text = "Error: could not reach the platform.";
        return updated;
      });
    } finally {
      setStreaming(false);
      isSendingRef.current = false;
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: "0 auto" }}>
      <div
        style={{
          minHeight: 320,
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          marginBottom: 12,
          background: "#fafafa",
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: "#888" }}>
            Ask something like "What is our vacation policy?" or "What's the
            status of TICKET-101?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ margin: "8px 0", textAlign: m.role === "user" ? "right" : "left" }}>
            <span
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: 12,
                background: m.role === "user" ? "#0f6e56" : "#e6e6e6",
                color: m.role === "user" ? "white" : "black",
                maxWidth: "80%",
                whiteSpace: "pre-wrap",
              }}
            >
              {m.text}
              {m.role === "assistant" && streaming && i === messages.length - 1 && (
                <span style={{ opacity: 0.5 }}>▍</span>
              )}
            </span>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleSend();
  }
}}
          placeholder="Type your question..."
          disabled={streaming}
          style={{ flex: 1, padding: 10, borderRadius: 6, border: "1px solid #ccc" }}
        />
        <button
          onClick={handleSend}
          disabled={streaming}
          style={{
            padding: "10px 20px",
            borderRadius: 6,
            border: "none",
            background: streaming ? "#999" : "#0f6e56",
            color: "white",
            cursor: streaming ? "default" : "pointer",
          }}
        >
          {streaming ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}