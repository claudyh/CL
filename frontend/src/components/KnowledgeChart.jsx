import React, { useState } from "react";
import "./KnowledgeChart.css";

export default function KnowledgeChart({ onChange }) {
    const [selectedCategories, setSelectedCategories] = useState([]);
    const categories = ["Monarchs", "Battles", "Treaties"];

    const toggleCategory = (cat) => {
        setSelectedCategories((prev) => {
            const newSelection = prev.includes(cat)
                ? prev.filter((c) => c !== cat)
                : [...prev, cat];
            onChange?.({ selectedCategories: newSelection });
            return newSelection;
        });
    };

    return (
        <svg className="knowledge-chart" width="300" height="300" viewBox="0 0 300 300">
            <g transform="translate(150,150)">
                {/* Outer circle segments */}
                {categories.map((cat, i) => {
                    const startAngle = (i * 120) * (Math.PI / 180);
                    const endAngle = ((i + 1) * 120) * (Math.PI / 180);
                    const radiusOuter = 140;
                    const radiusInner = 85;

                    const x1 = radiusInner * Math.cos(startAngle);
                    const y1 = radiusInner * Math.sin(startAngle);
                    const x2 = radiusOuter * Math.cos(startAngle);
                    const y2 = radiusOuter * Math.sin(startAngle);
                    const x3 = radiusOuter * Math.cos(endAngle);
                    const y3 = radiusOuter * Math.sin(endAngle);
                    const x4 = radiusInner * Math.cos(endAngle);
                    const y4 = radiusInner * Math.sin(endAngle);

                    const pathData = `
            M ${x1} ${y1}
            L ${x2} ${y2}
            A ${radiusOuter} ${radiusOuter} 0 0 1 ${x3} ${y3}
            L ${x4} ${y4}
            A ${radiusInner} ${radiusInner} 0 0 0 ${x1} ${y1}
            Z
          `;

                    const midAngle = startAngle + (endAngle - startAngle) / 2;
                    const radiusText = (radiusInner + radiusOuter) / 2;
                    const xText = radiusText * Math.cos(midAngle);
                    const yText = radiusText * Math.sin(midAngle);

                    const isSelected = selectedCategories.includes(cat);

                    return (
                        <g key={cat}>
                            <path
                                d={pathData}
                                className={`outer-segment ${isSelected ? "selected" : ""}`}
                                onClick={() => toggleCategory(cat)}
                            />
                            <text
                                x={xText}
                                y={yText}
                                className="outer-label"
                            >
                                {cat}
                            </text>
                        </g>
                    );
                })}

                {/* Center circle */}
                <circle r="85" className="knowledge-circle" />
                <text className="knowledge-label" textAnchor="middle">
                    <tspan x="0" dy="0">Knowledge Domain:</tspan>
                    <tspan x="0" dy="18">Portugal</tspan>
                </text>
            </g>
        </svg>
    );
}
