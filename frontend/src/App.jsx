import "./App.css";
import { useState, useEffect } from "react";
import logo from "./assets/logo.png";
import TimeScroller from "./components/TimeScroller";
import GraphView from "./components/GraphView";
import Stars from "./components/Stars";
import SearchBar from "./components/SearchBar";
import Timeline from "./components/Timeline";
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


    const [query, setQuery] = useState("");
    const [searchMessage, setSearchMessage] = useState("");

    const handleSearch = (text) => {
        if (!text.trim()) return;
        setSearchMessage(text);
    };

    const [inputValue, setInputValue] = useState("");
    const [submittedValue, setSubmittedValue] = useState("");

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
                <div className="searchbar-wrapper">
                    <SearchBar
                        value={inputValue}
                        onChange={setInputValue}
                        onSearch={(text) => setSubmittedValue(text)}
                    />
                </div>

                <div className="right-scroll-area">
                    {submittedValue && (
                        <Timeline
                            key={submittedValue}
                            years={["Past", "Present", "Future"]}
                            answers={[
                                "User searched: " + submittedValue,
                                "User searched: " + submittedValue,
                                "User searched: " + submittedValue
                            ]}
                        />
                    )}
                </div>
            </div>

        </div>
    );
}