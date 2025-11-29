import React, { useState } from "react";
import "./RatingDots.css";

export default function RatingDots({ onRate }) {
    const [rating, setRating] = useState(0);

    const handleClick = (value) => {
        setRating(value);
        onRate?.(value);
    };

    return (
        <div className="rating-wrapper">
            <span className="rating-label">Rate the answer:</span>
            <span className="rating-text">Bad</span>
            <div className="rating-container">
                {[1, 2, 3, 4, 5].map((value) => (
                    <div
                        key={value}
                        className={`rating-dot ${rating >= value ? "filled" : ""}`}
                        onClick={() => handleClick(value)}
                    />
                ))}
            </div>
            <span className="rating-text">Good</span>
        </div>
    );
}
