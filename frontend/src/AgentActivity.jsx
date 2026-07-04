import { useEffect, useState } from "react";
import { getAgents } from "./api";

export default function AgentActivity() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    getAgents().then(setAgents).catch(() => setAgents([]));
  }, []);

  return (
    <div>
      <h3 style={{ marginBottom: 12 }}>Registered Agents</h3>
      {agents.length === 0 && <p style={{ color: "#888" }}>No agents found.</p>}
      <div style={{ display: "grid", gap: 12 }}>
        {agents.map((a, i) => (
          <div
            key={i}
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              background: "#fafafa",
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 16, textTransform: "capitalize" }}>
              {a.name.replace("_", " ")}
            </div>
            <div style={{ color: "#666", marginTop: 4 }}>{a.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
}