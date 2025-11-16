import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import "./GraphView.css";

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
            "text-valign": "bottom",    // move label below node
            "text-halign": "center",
            "text-margin-y": 6,         // space between node and label
            "background-color": "#94a3b8",
            color: "#0f172a",
            "overlay-opacity": 0,
            width: 36,
            height: 36
          }
        },
        {
          selector: "node[type = 'Person']",
          style: { "background-color": "#65B1E9", color: "#65B1E9" }
        },
        {
          selector: "node[type = 'Country']",
          style: { "background-color": "#60C4AB", color: "#60C4AB" }
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
            "line-color": "#3B6A92",
            width: 2,
            "font-size": 10,
            "text-rotation": "autorotate",
            "text-margin-y": -10,          // move label above the edge
            color: "#3B6A92",               // text color white
            "text-background-opacity": 0,   // no box
            "text-background-padding": 0    // no padding
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

    // --- Floating animation starts here ---
    const floats = [];

    cy.nodes().forEach((node, i) => {
      const amplitude = 2 + Math.random() * 2;
      const speed = 0.0008 + Math.random() * 0.0015;
      const phase = Math.random() * 2 * Math.PI;
      const originalY = node.position("y");

      floats.push({ node, amplitude, speed, phase, originalY });
    });

    // Update originalY when node is released
    cy.nodes().on("free", (evt) => {
      const node = evt.target;
      const floatObj = floats.find(f => f.node.id() === node.id());
      if (floatObj) floatObj.originalY = node.position("y");
    });

    let startTime = null;
    function animate(time) {
      if (!startTime) startTime = time;

      floats.forEach(f => {
        if (!f.node.grabbed()) {
          const delta = Math.sin((time * f.speed) + f.phase) * f.amplitude;
          f.node.position("y", f.originalY + delta);
        }
      });

      requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
    // --- Floating animation ends here ---

    cy.fit(cy.elements(), 30);
  }, [nodes, edges]);

  return <div ref={containerRef} className="graph-container" />;
}