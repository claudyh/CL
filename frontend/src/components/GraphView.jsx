import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

export default function GraphView({ nodes, edges }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    const cy = cytoscape({
      container: containerRef.current,
      wheelSensitivity: 0.2,
      selectionType: "single",
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 12,
            "text-valign": "center",
            "text-halign": "center",
            "text-margin-y": "-2px",
            "background-color": "#94a3b8",
            color: "#0f172a",
            "border-width": 2,
            "border-color": "#ffffff",
            "overlay-opacity": 0,
            width: 36, height: 36
          }
        },
        {
          selector: "node[type = 'Person']",
          style: { "background-color": "#3b82f6", color: "#ffffff" }
        },
        {
          selector: "node[type = 'Country']",
          style: { "background-color": "#10b981", color: "#ffffff" }
        },
        {
          selector: "node[type = 'Position']",
          style: { "background-color": "#64748b", color: "#ffffff" }
        },
        {
          selector: "edge",
          style: {
            label: "data(label)",
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
            width: 2, "font-size": 10,
            "text-rotation": "autorotate",
            "text-margin-y": -6,
            "text-background-color": "#ffffff",
            "text-background-opacity": 0.9,
            "text-background-padding": 2
          }
        },
        {
          selector: "node:selected",
          style: { "border-color": "#f59e0b", "border-width": 3, "shadow-blur": 8, "shadow-opacity": 0.4 }
        }
      ],
      layout: { name: "cose", idealEdgeLength: 120, nodeRepulsion: 8000 },
      elements: []
    });

    cyRef.current = cy;
    return () => cy.destroy();
  }, []);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.elements().remove();

    const cyNodes = (nodes || []).map(n => ({
      data: { id: n.id, label: n.label, type: n.type || "Position" }
    }));
    const cyEdges = (edges || []).map(e => ({
      data: { source: e.source, target: e.target, label: e.label || "" }
    }));

    cy.add([...cyNodes, ...cyEdges]);
    const layout = cy.layout({ name: "cose", idealEdgeLength: 120, nodeRepulsion: 8000 });
    layout.run();
    cy.fit(cy.elements(), 30);
  }, [nodes, edges]);

  return <div ref={containerRef} className="graph-container" />;
}