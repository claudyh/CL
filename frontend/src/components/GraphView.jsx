import React, { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import "./GraphView.css";

export default function GraphView({ nodes, edges }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Initialize Cytoscape once
  useEffect(() => {
    const cy = cytoscape({
      container: containerRef.current,
      wheelSensitivity: 0.2,
      selectionType: "single",
      style: [
        // Default node style
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 12,
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 6,
            "background-color": "#94a3b8",
            color: "#0f172a",
            "overlay-opacity": 0,
            width: 36,
            height: 36
          }
        },

        // Node styles by type
        { selector: "node[type = 'Person']", style: { "background-color": "rgba(126, 129, 218, 1)", color: "rgba(126, 129, 218, 1)" } },
        { selector: "node[type = 'Country']", style: { "background-color": "#60C4AB", color: "#60C4AB" } },

        // NEW: Event type
        { selector: "node[type = 'Event']", style: { "background-color": "#65B1E9", color: "#65B1E9" } },

        // Edge style
        {
          selector: "edge",
          style: {
            label: "data(label)",
            "curve-style": "bezier",
            "line-color": "#3B6A92",
            width: 2,
            "font-size": 10,
            "text-rotation": "autorotate",
            "text-margin-y": -10,
            color: "#3B6A92"
          }
        },

        // Node selection behavior
        {
          selector: "node:selected",
          style: {
            shape: "ellipse",

            /* overlay ring */
            "overlay-shape": "ellipse",
            "overlay-color": "rgba(101, 177, 233, 0.23)",
            "overlay-padding": 2,
            "overlay-opacity": 0.45,

            /* brightened fill */
            "background-color": "rgba(0, 89, 255, 1)",
            "background-opacity": 0.95,

            /* transitions */
            "transition-property": "border-width, border-color, overlay-opacity, overlay-padding, background-color",
            "transition-duration": "200ms"
          }
        }
      ],
      layout: { name: "cose", idealEdgeLength: 120, nodeRepulsion: 8000 },
      elements: []
    });

    cyRef.current = cy;

    return () => cy.destroy();
  }, []);

  // Update graph whenever nodes/edges change
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.elements().remove();

    const cyNodes = nodes.map(n => ({
      data: { id: n.id, label: n.label, type: n.type || "Event" }
    }));

    const cyEdges = edges.map(e => ({
      data: { source: e.source, target: e.target, label: e.label || "" }
    }));

    cy.add([...cyNodes, ...cyEdges]);

    // Run layout
    const layout = cy.layout({ name: "cose", idealEdgeLength: 120, nodeRepulsion: 8000 });
    layout.run();

    layout.on("layoutstop", () => {
      cy.fit(cy.elements(), 30);
    });

    // Floating animation
    const floats = [];
    cy.nodes().forEach(node => {
      floats.push({
        node,
        amplitude: 2 + Math.random() * 2,
        speed: 0.0008 + Math.random() * 0.0015,
        phase: Math.random() * 2 * Math.PI,
        originalY: node.position("y")
      });
    });

    cy.nodes().on("free", evt => {
      const n = evt.target;
      const f = floats.find(f => f.node.id() === n.id());
      if (f) f.originalY = n.position("y");
    });

    function animate(time) {
      floats.forEach(f => {
        if (!f.node.grabbed()) {
          const d = Math.sin(time * f.speed + f.phase) * f.amplitude;
          f.node.position("y", f.originalY + d);
        }
      });
      requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }, [nodes, edges]);

  // Node selection events
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.on("tap", "node", evt => {
      const node = evt.target;
      setSelectedNode({
        id: node.id(),
        label: node.data("label"),
        type: node.data("type")
      });
    });

    cy.on("tap", evt => {
      if (evt.target === cy) setSelectedNode(null);
    });
  }, []);

  return (
    <>
      <div ref={containerRef} className="graph-container" />

      {selectedNode && (
        <div className="info-panel fixed-bottom-right">
          <div className="info-title">{selectedNode.label}</div>
          <div className="info-type">Type: {selectedNode.type}</div>

          <div className="info-section">
            <div className="info-label">Example Data:</div>
            <div className="info-value">Start: 1500</div>
            <div className="info-value">End: 1520</div>
          </div>
        </div>
      )}
    </>
  );
}
