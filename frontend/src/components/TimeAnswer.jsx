import React from "react";
import "./TimeAnswer.css";

export default function TimeAnswer({ message }) {
    return (
        <div className="timeanswer-wrapper">
            <div className="timeanswer-line" />

            <div className="timeanswer-column">
                <div className="timeanswer-dot" />
                <div className="timeanswer-label">Past</div>
                <div className="timeanswer-text">User searched: {message}</div>
            </div>

            <div className="timeanswer-column">
                <div className="timeanswer-dot" />
                <div className="timeanswer-label">Present</div>
                <div className="timeanswer-text">User searched: {message}</div>
            </div>

            <div className="timeanswer-column">
                <div className="timeanswer-dot" />
                <div className="timeanswer-label">Future</div>
                <div className="timeanswer-text">User searched: {message}</div>
            </div>
        </div>
    );
}
