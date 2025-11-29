import "./App.css";
import { useState, useEffect } from "react";
import logo from "./assets/logo.png";
import TimeScroller from "./components/TimeScroller";
import GraphView from "./components/GraphView";
import Stars from "./components/Stars";
import SearchBar from "./components/SearchBar";
import Timeline from "./components/Timeline";
import axios from "axios";
import KnowledgeChart from "./components/KnowledgeChart";

export default function App() {
    const [year, setYear] = useState(1605);
    const [graph, setGraph] = useState({ nodes: [], edges: [] });
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");
    const [previewYear, setPreviewYear] = useState(year);
    const isSliding = previewYear !== year;

    const [inputValue, setInputValue] = useState("");
    const [submittedValue, setSubmittedValue] = useState("");
    const [timelineData, setTimelineData] = useState({ years: [], answers: [] });
    const [timelineLoading, setTimelineLoading] = useState(false);

    useEffect(() => {
        if (!submittedValue) return;

        const fetchAnswer = async () => {
            setTimelineLoading(true);
            try {
                const res = await axios.post("http://localhost:5000/ask", {
                    question: submittedValue,
                });

                setTimelineData({
                    years: res.data.years,
                    answers: res.data.answers,
                });
            } catch (e) {
                console.error(e);
            } finally {
                setTimelineLoading(false);
            }
        };

        fetchAnswer();
    }, [submittedValue]);

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

    useEffect(() => {
        const delay = setTimeout(() => {
            // Only fetch when user stops sliding
            fetchYear(previewYear);
        }, 400); // adjust delay (300–500ms recommended)

        return () => clearTimeout(delay);
    }, [previewYear]); // runs when sliding finishes

    return (
        <div className="app">
            <div className="left">
                <Stars count={100} />
                {/* Logo top-left */}
                <img src={logo} alt="Logo" className="logo" />

                {/* Graph at top-center */}
                <div className="graph-wrapper">
                    {(loading || isSliding) && <div className="loading">Loading…</div>}

                    {!loading && !isSliding && !err && (
                        <GraphView nodes={graph.nodes} edges={graph.edges} />
                    )}

                    {err && <div className="error">{err}</div>}
                </div>

                {/* TimeScroller at bottom */}
                <div className="timeline-container">
                    <TimeScroller
                        minYear={1185}
                        maxYear={2025}
                        initialYear={year}
                        onYearSelected={(y) => {
                            setPreviewYear(y);
                        }}
                    />
                </div>
            </div>

            <div className="right-card">
                <div className="knowledge-chart-wrapper">
                    <KnowledgeChart onChange={(data) => console.log(data)} />
                </div>

                <div className="searchbar-wrapper">
                    <SearchBar
                        value={inputValue}
                        onChange={setInputValue}
                        onSearch={(text) => {
                            setTimelineData({ years: [], answers: [] }); // clear old answers
                            setSubmittedValue(text);
                        }}
                    />
                </div>

                <div className="right-scroll-area">
                    {timelineLoading && (
                        <div className="loading" style={{ paddingTop: "40px", textAlign: "center", fontSize: "18px" }}>
                            Loading answer…
                        </div>
                    )}

                    {timelineData.years.length > 0 && !timelineLoading && (
                        <Timeline
                            key={submittedValue}
                            years={timelineData.years}
                            answers={timelineData.answers}
                        />
                    )}
                </div>
            </div>

        </div>
    );
}