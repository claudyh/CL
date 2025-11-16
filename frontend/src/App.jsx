import "./App.css";
import { useState, useEffect } from "react";
import logo from "./assets/logo.png";
import TimeScroller from "./components/TimeScroller";
import GraphView from "./components/GraphView";
import Stars from "./components/Stars";
import axios from "axios";

export default function App() {
    const [year, setYear] = useState(1605);
    const [graph, setGraph] = useState({ nodes: [], edges: [] });
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    // fetch graph for specific year
    const fetchYear = async (y) => {
        try {
            setLoading(true);
            setErr("");
            const res = await axios.get(`http://localhost:5000/graph/${y}`);
            setGraph(res.data);
            setYear(y);
        } catch (e) {
            setErr(e?.message || "Failed to load graph");
        } finally {
            setLoading(false);
        }
    };

    // user moves the timeline → update year + graph
    const handleYearSelected = (y) => {
        if (Number.isFinite(y)) fetchYear(y);
    };

    // initial load
    useEffect(() => {
        fetchYear(year);
    }, []);

    return (
        <div className="app">
        <div className="left">
            <Stars count={100} />
            {/* Logo top-left */}
            <img src={logo} alt="Logo" className="logo" />
            
            {/* Graph at top-center */}
            <div className="graph-wrapper">
                {loading && <div className="loading">Loading…</div>}
                {err && <div className="error">{err}</div>}
                {!loading && !err && (
                    <GraphView nodes={graph.nodes} edges={graph.edges} />
                )}
            </div>
            
            {/* TimeScroller at bottom */}
            <div className="timeline-container">
            <TimeScroller
                minYear={1185}
                maxYear={2025}
                initialYear={year}
                onYearSelected={handleYearSelected}
            />
            </div>
        </div>
        <div className="right-card">
            <h2>My Card</h2>
            <p>Some content here...</p>
        </div>
        </div>
    );
}