import React, { useRef, useState, useEffect } from "react";
import "./TimeScroller.css";

export default function TimeScroller({
  minYear = 1185,
  maxYear = 2025,
  initialYear = 1605,
  onYearSelected
}) {
  const timelineRef = useRef(null);
  const pinRef = useRef(null);
  const [year, setYear] = useState(initialYear);
  const [dragging, setDragging] = useState(false);

  // convert year to percentage of timeline
  const yearToPercent = (y) => ((y - minYear) / (maxYear - minYear)) * 100;

  // convert x coordinate to year
  const xToYear = (x, width) => {
    let pct = x / width;
    if (pct < 0) pct = 0;
    if (pct > 1) pct = 1;
    return Math.round(minYear + pct * (maxYear - minYear));
  };

  const handleMouseDown = () => setDragging(true);
  const handleMouseUp = () => setDragging(false);

  const handleMouseMove = (e) => {
    if (!dragging) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const newYear = xToYear(e.clientX - rect.left, rect.width);
    setYear(newYear);
    onYearSelected?.(newYear);
  };

  // attach global mouse move/up events when dragging
  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [dragging]);

  // click on timeline jumps the pin
  const handleClick = (e) => {
    const rect = timelineRef.current.getBoundingClientRect();
    const newYear = xToYear(e.clientX - rect.left, rect.width);
    setYear(newYear);
    onYearSelected?.(newYear);
  };

  return (
    <div className="timeline-wrapper">
      <div ref={timelineRef} className="timeline-bar" onClick={handleClick}>
        <div
          ref={pinRef}
          className="pin"
          style={{ left: `${yearToPercent(year)}%` }}
          onMouseDown={handleMouseDown}
        >
          <span className="year-label">{year}</span>
        </div>
      </div>
    </div>
  );
}
