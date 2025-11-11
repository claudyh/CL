// Simple App component
import "./App.css";
import { useState } from "react";
import logo from "./assets/logo.png";
import TimeScroller from "./components/TimeScroller";

export default function App() {
    const [year, setYear] = useState(1605);

    return (
        <div className="app">
        <div className="left">
            {/* Logo top-left */}
            <img src={logo} alt="Logo" className="logo" />
            
            {/* TimeScroller at bottom */}
            <div className="timeline-container">
            <TimeScroller
                minYear={1185}
                maxYear={2025}
                initialYear={year}
                onYearSelected={(y) => setYear(y)}
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