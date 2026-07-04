import { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { getEvalResults } from "./api";

const COLORS = { pass: "#0f6e56", fail: "#993c1d" };

export default function EvalResults() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  async function runEvals() {
    setLoading(true);
    try {
      const result = await getEvalResults();
      setData(result);
    } catch (e) {
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  const chartData = data
    ? [
        { name: "Passed", value: data.passed },
        { name: "Failed", value: data.total - data.passed },
      ]
    : [];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Evaluation Results</h3>
        <button
          onClick={runEvals}
          disabled={loading}
          style={{ padding: "6px 14px", borderRadius: 6, border: "1px solid #ccc", cursor: "pointer" }}
        >
          {loading ? "Running..." : "Run Evaluations"}
        </button>
      </div>

      {!data && !loading && (
        <p style={{ color: "#888" }}>Click "Run Evaluations" to score the platform live.</p>
      )}

      {data && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 20 }}>
            <div style={{ width: 200, height: 200 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={chartData} dataKey="value" nameKey="name" outerRadius={80} label>
                    <Cell fill={COLORS.pass} />
                    <Cell fill={COLORS.fail} />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ fontSize: 32, fontWeight: 700 }}>
              {data.passed} / {data.total}
              <div style={{ fontSize: 14, fontWeight: 400, color: "#888" }}>tests passed</div>
            </div>
          </div>

          {data.results.map((r, i) => (
            <div
              key={i}
              style={{
                border: `1px solid ${r.passed ? "#0f6e56" : "#993c1d"}`,
                borderRadius: 8,
                padding: 12,
                marginBottom: 8,
              }}
            >
              <div style={{ fontWeight: 600 }}>
                {r.passed ? "✅" : "❌"} {r.id}
              </div>
              <div style={{ fontSize: 13, color: "#555", marginTop: 4 }}>{r.question}</div>
              <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>{r.reasoning}</div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}