const API_BASE = "http://localhost:8000";

export async function askQuestion(question) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

export async function getAuditLog() {
  const res = await fetch(`${API_BASE}/audit-log`);
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

export async function getAgents() {
  const res = await fetch(`${API_BASE}/agents`);
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

export async function getEvalResults() {
  const res = await fetch(`${API_BASE}/eval-results`);
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}