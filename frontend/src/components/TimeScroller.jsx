import React, { useEffect, useRef } from "react";
import { Timeline } from "vis-timeline/standalone";
import "vis-timeline/styles/vis-timeline-graph2d.css";

export default function TimeScroller({
  onYearSelected,
  minYear = 1100,
  maxYear = 2025,
  initialYear = 1185
}) {
  const ref = useRef(null);
  const timelineRef = useRef(null);

  useEffect(() => {
    const items = [];
    for (let y = minYear; y <= maxYear; y++) {
      items.push({ id: String(y), content: String(y), start: new Date(y, 0, 1) });
    }

    const tl = new Timeline(ref.current, items, {
      zoomable: true,
      horizontalScroll: true,
      zoomKey: "ctrlKey",
      selectable: true,
      stack: false,
      min: new Date(minYear, 0, 1),
      max: new Date(maxYear, 11, 31),
      timeAxis: { scale: "year", step: 5 }
    });

    const initId = String(initialYear);
    tl.setSelection([initId], { focus: true });

    tl.on("select", (ev) => {
      const id = ev.items?.[0];
      if (id) onYearSelected?.(parseInt(id, 10));
    });

    timelineRef.current = tl;
    return () => tl.destroy();
  }, [minYear, maxYear, initialYear, onYearSelected]);

  return (
    <div className="card">
      <div className="card__title">
        <span>Timeline</span>
        <span className="muted">Ctrl/Cmd + scroll to zoom</span>
      </div>
      <div ref={ref} className="timeline" />
    </div>
  );
}