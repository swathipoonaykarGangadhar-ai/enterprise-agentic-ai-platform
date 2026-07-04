import { useEffect, useState } from "react";
import { getAuditLog } from "./api";

export default function AuditLog() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await getAuditLog();
      setEntries(data);
    } catch (e) {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Audit Log</h3>
        <button onClick={load} style={{ padding: "6px 14px", borderRadius: 6, border: "1px solid #ccc", cursor: "pointer" }}>
          Refresh
        </button>
      </div>
      {loading && <p>Loading...</p>}
      {!loading && entries.length === 0 && (
        <p style={{ color: "#888" }}>No audit entries yet. Ask a question in the Chat tab first.</p>
      )}
      <div style={{ maxHeight: 500, overflowY: "auto" }}>
        {entries.map((e, i) => (
          <div
            key={i}
            style={{
              border: "1px solid #eee",
              borderRadius: 8,
              padding: 12,
              marginBottom: 8,
              fontSize: 13,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontWeight: 600 }}>{e.event_type}</span>
              <span style={{ color: "#888" }}>{e.timestamp}</span>
            </div>
            <div style={{ color: "#555" }}>Agent: {e.agent}</div>
            <div style={{ color: "#999", fontSize: 11, marginTop: 4 }}>
              trace: {e.trace_id}
            </div>
            <pre
              style={{
                background: "#f5f5f5",
                padding: 8,
                borderRadius: 6,
                marginTop: 6,
                overflowX: "auto",
                fontSize: 12,
              }}
            >
              {JSON.stringify(e.detail, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}