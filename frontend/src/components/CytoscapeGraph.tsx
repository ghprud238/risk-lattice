"use client";

import React, { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import { ZoomIn, ZoomOut, RefreshCw, Eye, ShieldAlert, Layers } from "lucide-react";

interface CytoscapeGraphProps {
  elements: {
    nodes: Array<{ data: any }>;
    edges: Array<{ data: any }>;
  };
  nodeShocks?: Record<string, any>;
  activeHop?: number | null;
  onNodeSelect?: (nodeData: any) => void;
}

export default function CytoscapeGraph({
  elements,
  nodeShocks = {},
  activeHop = null,
  onNodeSelect,
}: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [filterType, setFilterType] = useState<string>("ALL");

  useEffect(() => {
    if (!containerRef.current || !elements?.nodes?.length) return;

    // Filter elements based on type if selected
    let nodesToRender = elements.nodes;
    if (filterType !== "ALL") {
      nodesToRender = elements.nodes.filter(
        (n) => n.data.type === filterType
      );
    }
    const nodeIds = new Set(nodesToRender.map((n) => n.data.id));
    const edgesToRender = elements.edges.filter(
      (e) => nodeIds.has(e.data.source) && nodeIds.has(e.data.target)
    );

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...nodesToRender, ...edgesToRender],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-valign": "center",
            "text-halign": "center",
            color: "#ffffff",
            "font-size": "10px",
            "font-weight": "bold",
            "text-outline-width": 1.5,
            "text-outline-color": "#090d16",
            width: 38,
            height: 38,
            "border-width": 2,
            "border-color": "#475569",
            "background-color": "#1e293b",
            "transition-property": "background-color, border-color, width, height",
            "transition-duration": 0.3,
          },
        },
        {
          selector: "node[type = 'ASSET']",
          style: {
            "background-color": "#2563eb",
            "border-color": "#60a5fa",
            shape: "round-rectangle",
          },
        },
        {
          selector: "node[type = 'SUPPLIER']",
          style: {
            "background-color": "#d97706",
            "border-color": "#fbbf24",
            shape: "diamond",
            width: 44,
            height: 44,
          },
        },
        {
          selector: "node[type = 'MACRO']",
          style: {
            "background-color": "#9333ea",
            "border-color": "#c084fc",
            shape: "ellipse",
            width: 42,
            height: 42,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#334155",
            "target-arrow-color": "#334155",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            opacity: 0.6,
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 4,
            "border-color": "#38bdf8",
            "background-blacken": -0.2,
          },
        },
      ],
      layout: {
        name: "concentric",
        concentric: (node: any) => {
          const type = node.data("type");
          if (type === "MACRO") return 3;
          if (type === "SUPPLIER") return 2;
          return 1;
        },
        levelWidth: () => 1,
        padding: 40,
        animate: true,
        animationDuration: 500,
      },
    });

    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      const data = node.data();
      const shockInfo = nodeShocks[data.id] || null;
      const combined = { ...data, shockInfo };
      setSelectedNode(combined);
      if (onNodeSelect) onNodeSelect(combined);
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [elements, filterType]);

  // Update node colors & sizes dynamically when nodeShocks change
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    cy.batch(() => {
      cy.nodes().forEach((node) => {
        const id = node.data("id");
        const shock = nodeShocks[id];

        if (shock) {
          const val = shock.cumulative_shock || 0;
          if (val < -0.01) {
            // Negative shock -> Red
            const intensity = Math.min(1.0, Math.abs(val) / 0.5);
            node.style({
              "background-color": "#dc2626",
              "border-color": "#f87171",
              "border-width": 3 + intensity * 3,
            });
          } else if (val > 0.01) {
            // Positive impulse -> Emerald
            node.style({
              "background-color": "#059669",
              "border-color": "#34d399",
              "border-width": 3,
            });
          }
        }
      });
    });
  }, [nodeShocks]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleReset = () => {
    cyRef.current?.fit();
    cyRef.current?.center();
  };

  return (
    <div className="relative w-full h-[580px] bg-slate-950/90 rounded-xl border border-slate-800 overflow-hidden shadow-2xl flex flex-col">
      {/* Top Controls Bar */}
      <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="font-semibold text-slate-200 uppercase tracking-wider">
            50-Node Multi-Layer Dependency Canvas
          </span>
          <div className="flex items-center space-x-1 ml-4 bg-slate-800/80 rounded-lg p-0.5 border border-slate-700">
            {["ALL", "ASSET", "SUPPLIER", "MACRO"].map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition ${
                  filterType === t
                    ? "bg-cyan-500 text-slate-950 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded bg-blue-500 border border-blue-400"></span>
            <span className="text-slate-400 text-[11px]">Equities (20)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rotate-45 bg-amber-500 border border-amber-400"></span>
            <span className="text-slate-400 text-[11px]">Choke Nodes (20)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500 border border-purple-400"></span>
            <span className="text-slate-400 text-[11px]">Macro (10)</span>
          </div>

          <div className="flex items-center space-x-1 border-l border-slate-700 pl-3">
            <button
              onClick={handleZoomIn}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleReset}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
              title="Reset View"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Cytoscape DOM Canvas */}
      <div ref={containerRef} className="flex-1 w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Node Inspector Drawer */}
      {selectedNode && (
        <div className="absolute bottom-3 left-3 max-w-sm bg-slate-900/95 backdrop-blur border border-slate-700 rounded-lg p-3 text-xs shadow-xl animate-fade-in z-20">
          <div className="flex items-start justify-between">
            <div>
              <span className="font-bold text-sm text-cyan-400">{selectedNode.id}</span>
              <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                {selectedNode.type}
              </span>
              <p className="text-slate-300 mt-0.5">{selectedNode.name}</p>
              <p className="text-slate-400 text-[11px]">{selectedNode.sector}</p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-500 hover:text-slate-300 text-sm"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-3 pt-2 border-t border-slate-800 text-[11px]">
            <div>
              <span className="text-slate-400">Net Debt / EBITDA:</span>
              <span className="ml-1 text-slate-200 font-mono font-medium">
                {selectedNode.net_debt_ebitda}x
              </span>
            </div>
            <div>
              <span className="text-slate-400">Int Coverage:</span>
              <span className="ml-1 text-slate-200 font-mono font-medium">
                {selectedNode.int_coverage}x
              </span>
            </div>
            <div>
              <span className="text-slate-400">Substitutability (σ):</span>
              <span className="ml-1 text-slate-200 font-mono font-medium">
                {selectedNode.substitutability}
              </span>
            </div>
            {selectedNode.shockInfo && (
              <div>
                <span className="text-slate-400">Distress (λ):</span>
                <span className="ml-1 text-amber-400 font-mono font-bold">
                  {selectedNode.shockInfo.distress_multiplier}x
                </span>
              </div>
            )}
          </div>

          {selectedNode.shockInfo && (
            <div className="mt-2.5 pt-2 border-t border-slate-800">
              <div className="flex items-center justify-between font-mono">
                <span className="text-slate-400">Total Shock:</span>
                <span
                  className={`font-bold ${
                    selectedNode.shockInfo.cumulative_shock < 0
                      ? "text-red-400"
                      : "text-emerald-400"
                  }`}
                >
                  {(selectedNode.shockInfo.cumulative_shock * 100).toFixed(2)}%
                </span>
              </div>
              <div className="text-[10px] text-slate-400 grid grid-cols-3 gap-1 mt-1 font-mono">
                <div>1st: {(selectedNode.shockInfo.order1_direct * 100).toFixed(1)}%</div>
                <div>2nd: {(selectedNode.shockInfo.order2_tier1 * 100).toFixed(1)}%</div>
                <div>3/4th: {(selectedNode.shockInfo.order3_4_network * 100).toFixed(1)}%</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
