"use client";

import React, { useState, useEffect } from "react";
import {
  Globe2,
  ArrowRight,
} from "lucide-react";

interface Facility {
  id: string;
  ticker: string;
  name: string;
  lat: number;
  lng: number;
  city: string;
  country: string;
  type: string;
  criticality: number;
}

interface Corridor {
  from: string;
  to: string;
  mode: string;
  dependency: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

export default function GeospatialMap() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("ALL");

  useEffect(() => {
    const fetchGeo = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/graph/geospatial`);
        if (res.ok) {
          const data = await res.json();
          setFacilities(data.facilities || []);
          setCorridors(data.corridors || []);
          if (data.facilities?.length > 0) {
            setSelectedFacility(data.facilities[0]);
          }
        }
      } catch (e) {
        console.error("Failed to load geospatial graph", e);
      }
    };
    fetchGeo();
  }, []);

  const filteredFacilities = facilities.filter((f) => {
    if (activeFilter === "ALL") return true;
    return f.type === activeFilter;
  });

  // Map projection helpers (Mercator approximation to SVG coordinates)
  const mapWidth = 900;
  const mapHeight = 460;

  const project = (lat: number, lng: number) => {
    const x = ((lng + 180) * (mapWidth / 360));
    const latRad = (lat * Math.PI) / 180;
    const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
    const y = mapHeight / 2 - (mapWidth * mercN) / (2 * Math.PI);
    return { x: Math.max(10, Math.min(mapWidth - 10, x)), y: Math.max(10, Math.min(mapHeight - 10, y)) };
  };

  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <Globe2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Global Geospatial Physical Lattice &amp; Maritime Choke Points
            </h2>
            <p className="text-xs text-slate-400">
              PRD Section 16 • Geographic Fab Clusters, Maritime Straits &amp; Critical Transit Corridors
            </p>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          {["ALL", "FAB", "CHOKE_POINT", "PORT", "ASSEMBLY"].map((t) => (
            <button
              key={t}
              onClick={() => setActiveFilter(t)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                activeFilter === t
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {t.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Main Map Canvas & Drawer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SVG World Map */}
        <div className="lg:col-span-2 bg-slate-950/90 border border-slate-800 rounded-xl p-4 relative overflow-hidden flex flex-col justify-between min-h-[460px]">
          {/* Subtle Grid Background */}
          <div
            className="absolute inset-0 opacity-15 pointer-events-none"
            style={{
              backgroundImage: "radial-gradient(#38bdf8 1px, transparent 1px)",
              backgroundSize: "28px 28px",
            }}
          />

          <svg viewBox={`0 0 ${mapWidth} ${mapHeight}`} className="w-full h-auto">
            {/* World Land Outline Placeholder Curves */}
            <path
              d="M 120 120 Q 220 80 320 150 Q 260 280 200 320 Z"
              fill="#1e293b"
              opacity="0.3"
            />
            <path
              d="M 450 110 Q 550 90 620 160 Q 560 260 480 220 Z"
              fill="#1e293b"
              opacity="0.3"
            />
            <path
              d="M 640 120 Q 820 140 800 280 Q 700 360 620 280 Z"
              fill="#1e293b"
              opacity="0.3"
            />

            {/* Corridors / Supply Arcs */}
            {corridors.map((c, idx) => {
              const src = facilities.find((f) => f.id === c.from);
              const tgt = facilities.find((f) => f.id === c.to);
              if (!src || !tgt) return null;
              const p1 = project(src.lat, src.lng);
              const p2 = project(tgt.lat, tgt.lng);
              const midX = (p1.x + p2.x) / 2;
              const midY = Math.min(p1.y, p2.y) - 35;

              return (
                <g key={idx}>
                  <path
                    d={`M ${p1.x} ${p1.y} Q ${midX} ${midY} ${p2.x} ${p2.y}`}
                    fill="none"
                    stroke="#0284c7"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    opacity="0.75"
                  />
                  <circle cx={(p1.x + p2.x) / 2} cy={midY + 15} r="2" fill="#38bdf8" />
                </g>
              );
            })}

            {/* Facilities Nodes */}
            {filteredFacilities.map((f) => {
              const pos = project(f.lat, f.lng);
              const isSelected = selectedFacility?.id === f.id;
              const isChoke = f.type === "CHOKE_POINT";

              return (
                <g
                  key={f.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => setSelectedFacility(f)}
                  className="cursor-pointer group"
                >
                  {/* Ping Animation */}
                  <circle
                    r={isSelected ? "14" : isChoke ? "10" : "7"}
                    fill={isChoke ? "#f43f5e" : "#06b6d4"}
                    opacity="0.25"
                    className="animate-ping"
                  />
                  {/* Core Pin */}
                  <circle
                    r={isSelected ? "8" : isChoke ? "6" : "5"}
                    fill={isChoke ? "#e11d48" : isSelected ? "#38bdf8" : "#0ea5e9"}
                    stroke="#ffffff"
                    strokeWidth={isSelected ? "2" : "1"}
                  />
                  {/* Label */}
                  <text
                    y="-10"
                    textAnchor="middle"
                    fill="#e2e8f0"
                    fontSize="10"
                    fontFamily="monospace"
                    fontWeight="bold"
                    className="pointer-events-none drop-shadow"
                  >
                    {f.city}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Footer Legend */}
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                <span>Silicon Fab Cluster</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <span>Maritime Choke Point</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-400"></span>
                <span>Global Container Port</span>
              </span>
            </div>
            <span>Coordinates Projected (WGS84)</span>
          </div>
        </div>

        {/* Selected Facility Detail Drawer */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
          {selectedFacility ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    selectedFacility.type === "CHOKE_POINT"
                      ? "bg-rose-950 text-rose-400 border border-rose-800"
                      : "bg-cyan-950 text-cyan-400 border border-cyan-800"
                  }`}
                >
                  {selectedFacility.type}
                </span>
                <span className="text-[10px] font-mono text-slate-500">
                  {selectedFacility.ticker}
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-white">{selectedFacility.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {selectedFacility.city}, {selectedFacility.country}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Latitude / Longitude</div>
                  <div className="text-slate-300 font-bold mt-0.5">
                    {selectedFacility.lat.toFixed(3)}°, {selectedFacility.lng.toFixed(3)}°
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Criticality Score</div>
                  <div className="text-rose-400 font-bold mt-0.5">
                    {(selectedFacility.criticality * 100).toFixed(0)}% Vital
                  </div>
                </div>
              </div>

              {/* Transit Dependencies */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-300">Active Supply Connections</div>
                <div className="space-y-1.5 text-xs font-mono">
                  {corridors
                    .filter((c) => c.from === selectedFacility.id || c.to === selectedFacility.id)
                    .map((c, i) => (
                      <div
                        key={i}
                        className="p-2 rounded bg-slate-950/60 border border-slate-800 flex items-center justify-between"
                      >
                        <span className="text-slate-300">
                          {c.from} <ArrowRight className="inline w-3 h-3 text-cyan-400" /> {c.to}
                        </span>
                        <span className="text-[10px] text-cyan-400 font-bold">
                          {(c.dependency * 100).toFixed(0)}% Flow
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs font-mono">
              Click any map node to inspect facility parameters
            </div>
          )}

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
            Physical bottlenecks are tracked via satellite AIS and live SEC 10-K production disclosures.
          </div>
        </div>
      </div>
    </div>
  );
}
