import React from "react";
import "./Timeline.css";

export default function Timeline({ years, answers }) {

    return (
        <div className="tl-wrapper">
            {years.map((year, i) => (
                <div className="tl-entry" key={i}>

                    {/* Line segment before the dot */}
                    <div
                        className="tl-line-segment"
                        style={{ animationDelay: `${i * 0.9}s` }}
                    />

                    {/* Dot */}
                    <div
                        className="tl-dot"
                        style={{ animationDelay: `${i * 0.9 + 0.7}s` }}
                    />

                    {/* Label + text */}
                    <div className="tl-text-block">
                        <div
                            className="tl-label"
                            style={{ animationDelay: `${i * 0.9 + 0.8}s` }}
                        >
                            {year}
                        </div>

                        <div
                            className="tl-text"
                            style={{ animationDelay: `${i * 0.9 + 1.0}s` }}
                        >
                            {answers[i]}
                        </div>
                    </div>
                </div>
            ))}

            {/* Final line tail after last dot */}
            <div
                className="tl-line-segment"
                style={{ animationDelay: `${years.length * 0.9}s` }}
            />
        </div>
    );
}
