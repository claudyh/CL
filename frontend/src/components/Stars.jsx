// src/components/Stars.jsx
import React, { useEffect, useState } from "react";
import "./Stars.css";

export default function Stars({ count = 50 }) {
  const [stars, setStars] = useState([]);

  useEffect(() => {
    const newStars = Array.from({ length: count }, () => ({
      top: Math.random() * 100, // percentage
      left: Math.random() * 100, // percentage
      size: Math.random() * 2 + 1, // 1px - 3px
      delay: Math.random() * 5, // seconds
      duration: Math.random() * 5 + 5, // 5s - 10s
    }));
    setStars(newStars);
  }, [count]);

  return (
    <div className="stars-container">
      {stars.map((star, i) => (
        <div
          key={i}
          className="star"
          style={{
            top: `${star.top}%`,
            left: `${star.left}%`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            animationDelay: `${star.delay}s`,
            animationDuration: `${star.duration}s`,
          }}
        ></div>
      ))}
    </div>
  );
}
