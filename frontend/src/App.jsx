import React, { useMemo, useState } from "react";
import axios from "axios";
import GraphView from "./components/GraphView";
import TimeScroller from "./components/TimeScroller";
import Legend from "./components/Legend";
import "./styles.css";

function Badge({ children }) {
  return <span className="badge">{children}</span>;
}

export default function App() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [year, setYear] = useState(1185);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const nodeCount = graph?.nodes?.length || 0;
  const edgeCount = graph?.edges?.length || 0;

  const fetchYear = async (y) => {
    try {
      setLoading(true);
      setErr("");
      // If using Vite proxy, you can call `/graph/${y}` directly:
      const res = await axios.get(`http://localhost:5000/graph/${y}`);
      setGraph(res.data);
      setYear(y);
    } catch (e) {
      setErr(e?.message || "Failed to load graph");
    } finally {
      setLoading(false);
    }
  };

  const handleYearSelected = (y) => {
    if (Number.isFinite(y)) fetchYear(y);
  };

  useMemo(() => { fetchYear(year); /* run once on mount */ }, []);

  return (
    <>
      <header className="app-header">
        <div className="app-header__inner">
          <div>
            <h1 className="app-title">ChronoGraph</h1>
            <p className="app-sub">Explore Portuguese monarchs and positions across time.</p>
          </div>
          <div className="badges">
            <Badge>Year: {year}</Badge>
            <Badge>Nodes: {nodeCount}</Badge>
            <Badge>Edges: {edgeCount}</Badge>
          </div>
        </div>
      </header>

      <main className="app-main">
        {err ? (
          <div className="card" style={{ border: "1px solid #fecaca", background: "#fef2f2" }}>
            <div style={{ color: "#b91c1c", fontSize: 14 }}>{err}</div>
          </div>
        ) : null}

        <div className="grid">
          <div className="left-col" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <TimeScroller onYearSelected={handleYearSelected} initialYear={year} />
            <Legend />
            <div className="card">
              <div className="card__title">Tips</div>
              <ul className="list">
                <li>Click a year to load the graph for that period.</li>
                <li>Drag to pan; use Ctrl/Cmd + scroll to zoom.</li>
              </ul>
            </div>
          </div>

          <div className="right-col">
            <div className="card" style={{ padding: 16 }}>
              <div className="card__title">
                <span>Graph</span>
                {loading ? (
                  <span className="muted">Loading…</span>
                ) : (
                  <button className="button" onClick={() => handleYearSelected(year)}>Refresh</button>
                )}
              </div>
              <GraphView nodes={graph.nodes || []} edges={graph.edges || []} />
            </div>
          </div>
        </div>
      </main>

      <footer style={{ marginTop: 28, padding: "18px 0", textAlign: "center", fontSize: 12, color: "#6b7280" }}>
        Data from RDF (Turtle) — rendered with Cytoscape & vis-timeline.
      </footer>
    </>
  );
}