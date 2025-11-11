import React from "react";

export default function Legend() {
  return (
    <div className="card">
      <div className="card__title">Legend</div>
      <div className="legend">
        <div className="legend__item">
          <span className="legend__swatch" style={{ background: "#3b82f6" }} />
          <span>Person</span>
        </div>
        <div className="legend__item">
          <span className="legend__swatch" style={{ background: "#10b981" }} />
          <span>Country</span>
        </div>
        <div className="legend__item">
          <span className="legend__swatch" style={{ background: "#64748b" }} />
          <span>Position</span>
        </div>
      </div>
    </div>
  );
}