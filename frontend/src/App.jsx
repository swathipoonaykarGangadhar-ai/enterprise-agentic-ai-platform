import { useState } from "react";
import Chat from "./Chat";
import AuditLog from "./AuditLog";
import EvalResults from "./EvalResults";
import AgentActivity from "./AgentActivity";

const TABS = [
  { id: "chat", label: "Chat", component: Chat },
  { id: "audit", label: "Audit Log", component: AuditLog },
  { id: "evals", label: "Eval Results", component: EvalResults },
  { id: "agents", label: "Agent Activity", component: AgentActivity },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const ActiveComponent = TABS.find((t) => t.id === activeTab).component;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: 4 }}>Enterprise Agentic AI Platform</h1>
      <p style={{ color: "#888", marginTop: 0, marginBottom: 24 }}>
        MCP · GraphRAG · Multi-Agent Orchestration · AI Governance · Evaluation · Kubernetes
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 24, borderBottom: "1px solid #ddd" }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "10px 18px",
              border: "none",
              background: "none",
              cursor: "pointer",
              fontSize: 15,
              fontWeight: activeTab === tab.id ? 700 : 400,
              borderBottom: activeTab === tab.id ? "2px solid #0f6e56" : "2px solid transparent",
              color: activeTab === tab.id ? "#0f6e56" : "#555",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <ActiveComponent />
    </div>
  );
}