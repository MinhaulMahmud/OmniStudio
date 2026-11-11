import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { EngineCrossSection } from "./EngineCrossSection";
import { SequentialGearboxMechanism } from "./SequentialGearboxMechanism";
import { GearWheel } from "./GearWheel";
import { MapViewport } from "../scenes/primitives/MapViewport";

export interface VisualMechanismViewportProps {
  topic: string;
  sectionIndex: number;
  totalSections: number;
  heading: string;
  width?: number;
  height?: number;
}

export const VisualMechanismViewport: React.FC<VisualMechanismViewportProps> = ({
  topic,
  sectionIndex,
  totalSections,
  heading,
  width = 680,
  height = 480,
}) => {
  const frame = useCurrentFrame();
  const lowerTopic = (topic + " " + heading).toLowerCase();

  const isMechanical =
    lowerTopic.includes("gear") ||
    lowerTopic.includes("engine") ||
    lowerTopic.includes("motor") ||
    lowerTopic.includes("transmission") ||
    lowerTopic.includes("bike") ||
    lowerTopic.includes("car") ||
    lowerTopic.includes("mechanical");

  const isAIOrCompute =
    lowerTopic.includes("model") ||
    lowerTopic.includes("weight") ||
    lowerTopic.includes("compute") ||
    lowerTopic.includes("vram") ||
    lowerTopic.includes("gpu") ||
    lowerTopic.includes("ai") ||
    lowerTopic.includes("neural");

  const isGeographic =
    lowerTopic.includes("map") ||
    lowerTopic.includes("trade") ||
    lowerTopic.includes("route") ||
    lowerTopic.includes("silk road") ||
    lowerTopic.includes("empire") ||
    lowerTopic.includes("country") ||
    lowerTopic.includes("continent") ||
    lowerTopic.includes("world") ||
    lowerTopic.includes("geography") ||
    lowerTopic.includes("travel") ||
    lowerTopic.includes("roman") ||
    lowerTopic.includes("voyage") ||
    lowerTopic.includes("shipping") ||
    lowerTopic.includes("territory");

  // ─── 0. GEOGRAPHIC & MAP ANIMATIONS (d3-geo + TopoJSON) ──────────────────
  if (isGeographic) {
    if (sectionIndex === 0) {
      return (
        <div
          style={{
            width: `${width}px`,
            height: `${height}px`,
            borderRadius: "20px",
            overflow: "hidden",
            border: "1px solid rgba(0, 229, 255, 0.35)",
            boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          }}
        >
          <MapViewport
            width={width}
            height={height}
            projectionType="equal-earth"
            center={[30, 25]}
            zoom={1.2}
            highlightCountries={[
              { id: "Italy", label: "Rome", appearAtFrame: 0 },
              { id: "Egypt", label: "Alexandria", appearAtFrame: 15 },
              { id: "Greece", label: "Athens", appearAtFrame: 30 },
            ]}
            pins={[
              { lngLat: [12.4964, 41.9028], label: "Rome", appearAtFrame: 5 },
              { lngLat: [29.9187, 31.2001], label: "Alexandria", appearAtFrame: 20 },
            ]}
            arcs={[
              { from: [12.4964, 41.9028], to: [29.9187, 31.2001], label: "Trade Route", appearAtFrame: 10 },
            ]}
          />
        </div>
      );
    } else {
      return (
        <div
          style={{
            width: `${width}px`,
            height: `${height}px`,
            borderRadius: "20px",
            overflow: "hidden",
            border: "1px solid rgba(0, 229, 255, 0.35)",
            boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          }}
        >
          <MapViewport
            width={width}
            height={height}
            projectionType="equal-earth"
            center={[45, 30]}
            zoom={1.4}
            highlightCountries={[
              { id: "Italy", appearAtFrame: 0 },
              { id: "Egypt", appearAtFrame: 0 },
              { id: "Turkey", appearAtFrame: 10 },
              { id: "Iran", appearAtFrame: 25 },
              { id: "China", appearAtFrame: 40 },
            ]}
            pins={[
              { lngLat: [12.4964, 41.9028], label: "Rome", appearAtFrame: 0 },
              { lngLat: [28.9784, 41.0082], label: "Constantinople", appearAtFrame: 15 },
              { lngLat: [116.4074, 39.9042], label: "Chang'an", appearAtFrame: 35 },
            ]}
            arcs={[
              { from: [12.4964, 41.9028], to: [28.9784, 41.0082], appearAtFrame: 5 },
              { from: [28.9784, 41.0082], to: [116.4074, 39.9042], appearAtFrame: 25, drawDurationFrames: 50 },
            ]}
          />
        </div>
      );
    }
  }

  // ─── 1. MECHANICAL & TRANSMISSION ANIMATIONS ─────────────────────────────
  if (isMechanical) {
    if (sectionIndex === 0) {
      // Stage 1: Engine Exterior & Combustion Cycle
      return (
        <div
          style={{
            width: `${width}px`,
            height: `${height}px`,
            backgroundColor: "#070b14",
            borderRadius: "20px",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <div
            style={{
              padding: "10px 16px",
              backgroundColor: "rgba(15, 23, 42, 0.8)",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              fontSize: "12px",
              fontWeight: 700,
              color: "#38bdf8",
              letterSpacing: "1px",
            }}
          >
            STAGE 1: 4-STROKE ENGINE CUTAWAY & CRANKCASE
          </div>
          <svg viewBox="0 0 520 380" style={{ width: "100%", height: "calc(100% - 35px)" }}>
            <EngineCrossSection scale={0.9} x={30} y={40} />
          </svg>
        </div>
      );
    } else if (sectionIndex === 1) {
      // Stage 2: Zooming Inside the Engine Casing
      const zoom = interpolate(frame, [0, 60], [1.0, 1.8], { extrapolateRight: "clamp" });
      const panX = interpolate(frame, [0, 60], [0, -140], { extrapolateRight: "clamp" });
      const panY = interpolate(frame, [0, 60], [0, -100], { extrapolateRight: "clamp" });

      return (
        <div
          style={{
            width: `${width}px`,
            height: `${height}px`,
            backgroundColor: "#070b14",
            borderRadius: "20px",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <div
            style={{
              padding: "10px 16px",
              backgroundColor: "rgba(15, 23, 42, 0.8)",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              fontSize: "12px",
              fontWeight: 700,
              color: "#38bdf8",
              letterSpacing: "1px",
            }}
          >
            STAGE 2: PENETRATING INTO TRANSMISSION CAVITY
          </div>
          <svg viewBox="0 0 520 380" style={{ width: "100%", height: "calc(100% - 35px)" }}>
            <g transform={`translate(${panX}, ${panY}) scale(${zoom})`}>
              <EngineCrossSection scale={0.9} x={30} y={40} highlightTransmission={true} />
            </g>
          </svg>
        </div>
      );
    } else {
      // Stage 3+: Full Working Constant Mesh Gearbox
      return (
        <SequentialGearboxMechanism
          width={width}
          height={height}
          inputRpm={6200}
          showTorquePath={true}
        />
      );
    }
  }

  // ─── 2. AI, MODEL WEIGHTS & GPU COMPUTE ANIMATIONS ───────────────────────
  if (isAIOrCompute) {
    if (sectionIndex === 0) {
      // Neural Matrix & Parameter Grid
      const nodes = [
        { x: 80, y: 100 }, { x: 80, y: 180 }, { x: 80, y: 260 }, { x: 80, y: 340 },
        { x: 260, y: 70 }, { x: 260, y: 150 }, { x: 260, y: 230 }, { x: 260, y: 310 }, { x: 260, y: 390 },
        { x: 440, y: 120 }, { x: 440, y: 220 }, { x: 440, y: 320 },
        { x: 600, y: 170 }, { x: 600, y: 270 },
      ];

      return (
        <div
          style={{
            width: `${width}px`,
            height: `${height}px`,
            backgroundColor: "#070b14",
            borderRadius: "20px",
            border: "1px solid rgba(99, 102, 241, 0.3)",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <div
            style={{
              padding: "10px 16px",
              backgroundColor: "rgba(15, 23, 42, 0.8)",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              fontSize: "12px",
              fontWeight: 700,
              color: "#818cf8",
              letterSpacing: "1px",
            }}
          >
            NEURAL NETWORK MATRIX // LEARNED SYNAPSE WEIGHTS [W]
          </div>
          <svg viewBox="0 0 680 440" style={{ width: "100%", height: "calc(100% - 35px)" }}>
            {/* Synaptic connection lines with animated signal pulses */}
            {nodes.slice(0, 4).map((n1, i) =>
              nodes.slice(4, 9).map((n2, j) => {
                const pulse = (frame * 3 + i * 15 + j * 10) % 100;
                return (
                  <g key={`${i}-${j}`}>
                    <line
                      x1={n1.x}
                      y1={n1.y}
                      x2={n2.x}
                      y2={n2.y}
                      stroke="rgba(99, 102, 241, 0.15)"
                      strokeWidth="1.5"
                    />
                    <circle
                      cx={n1.x + ((n2.x - n1.x) * pulse) / 100}
                      cy={n1.y + ((n2.y - n1.y) * pulse) / 100}
                      r="2"
                      fill="#38bdf8"
                      opacity="0.6"
                    />
                  </g>
                );
              })
            )}

            {nodes.slice(4, 9).map((n1, i) =>
              nodes.slice(9, 12).map((n2, j) => (
                <line
                  key={`${i}-${j}`}
                  x1={n1.x}
                  y1={n1.y}
                  x2={n2.x}
                  y2={n2.y}
                  stroke="rgba(168, 85, 247, 0.18)"
                  strokeWidth="1.5"
                />
              ))
            )}

            {/* Glowing Neural Nodes */}
            {nodes.map((n, i) => (
              <g key={i}>
                <circle cx={n.x} cy={n.y} r="14" fill="#0f172a" stroke="#818cf8" strokeWidth="2.5" />
                <circle cx={n.x} cy={n.y} r="6" fill="#38bdf8" />
              </g>
            ))}
          </svg>
        </div>
      );
    } else {
      // GPU Silicon Memory Bus Architecture (VRAM -> HBM3 Bus -> Tensor Cores)
      return (
        <div
          style={{
            width: `${width}px`,
            height: `${height}px`,
            backgroundColor: "#070b14",
            borderRadius: "20px",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            overflow: "hidden",
            position: "relative",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              padding: "10px 16px",
              backgroundColor: "rgba(15, 23, 42, 0.8)",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              fontSize: "12px",
              fontWeight: 700,
              color: "#f43f5e",
              letterSpacing: "1px",
            }}
          >
            GPU SILICON ARCHITECTURE // MEMORY BANDWIDTH BOTTLENECK
          </div>
          <svg viewBox="0 0 680 440" style={{ width: "100%", height: "calc(100% - 35px)" }}>
            {/* VRAM / HBM3 Stack */}
            <rect x={40} y={80} width={140} height={260} rx={12} fill="#1e1b4b" stroke="#6366f1" strokeWidth="2" />
            <text x={110} y={130} textAnchor="middle" fill="#c7d2fe" fontSize="16" fontWeight="800">
              VRAM (HBM3)
            </text>
            <text x={110} y={160} textAnchor="middle" fill="#818cf8" fontSize="13">
              140 GB Weights
            </text>
            <text x={110} y={220} textAnchor="middle" fill="#94a3b8" fontSize="12">
              (70B @ 2 Bytes)
            </text>

            {/* High-Speed Streaming Bus with flowing data packets */}
            <rect x={180} y={190} width={300} height={40} rx={8} fill="#0f172a" stroke="#f43f5e" strokeWidth="2" />
            <text x={330} y={215} textAnchor="middle" fill="#f43f5e" fontSize="13" fontWeight="800" letterSpacing="1px">
              MEMORY BUS: 3,350 GB/s
            </text>
            {[...Array(6)].map((_, i) => {
              const packetX = 190 + ((frame * 6 + i * 50) % 270);
              return <rect key={i} x={packetX} y={198} width={20} height={24} rx={4} fill="#fb7185" />;
            })}

            {/* Tensor Cores / Compute Silicon */}
            <rect x={480} y={80} width={160} height={260} rx={12} fill="#022c22" stroke="#10b981" strokeWidth="2" />
            <text x={560} y={130} textAnchor="middle" fill="#a7f3d0" fontSize="16" fontWeight="800">
              TENSOR CORES
            </text>
            <text x={560} y={160} textAnchor="middle" fill="#34d399" fontSize="13">
              ALU Matrix Math
            </text>
            <text x={560} y={220} textAnchor="middle" fill="#94a3b8" fontSize="12">
              Waiting on Weights!
            </text>
          </svg>
        </div>
      );
    }
  }

  // ─── 3. DEFAULT SYSTEM ARCHITECTURE VISUALIZER ───────────────────────────
  return (
    <div
      style={{
        width: `${width}px`,
        height: `${height}px`,
        backgroundColor: "#070b14",
        borderRadius: "20px",
        border: "1px solid rgba(56, 189, 248, 0.3)",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div
        style={{
          padding: "10px 16px",
          backgroundColor: "rgba(15, 23, 42, 0.8)",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          fontSize: "12px",
          fontWeight: 700,
          color: "#38bdf8",
          letterSpacing: "1px",
        }}
      >
        TECHNICAL ARCHITECTURE & MECHANISM WORKFLOW
      </div>
      <svg viewBox="0 0 680 440" style={{ width: "100%", height: "calc(100% - 35px)" }}>
        {/* Animated Signal Flow Lines */}
        <line x1={100} y1={220} x2={580} y2={220} stroke="#38bdf8" strokeWidth="3" strokeDasharray="8 6" strokeDashoffset={-frame * 3} />
        {/* Interactive Processing Blocks */}
        <rect x={80} y={160} width={140} height={120} rx={16} fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />
        <text x={150} y={225} textAnchor="middle" fill="#ffffff" fontWeight="700">INPUT STAGE</text>

        <rect x={270} y={140} width={140} height={160} rx={16} fill="#1e1b4b" stroke="#818cf8" strokeWidth="2.5" />
        <text x={340} y={225} textAnchor="middle" fill="#ffffff" fontWeight="800">PROCESSING</text>

        <rect x={460} y={160} width={140} height={120} rx={16} fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />
        <text x={530} y={225} textAnchor="middle" fill="#ffffff" fontWeight="700">OUTPUT STAGE</text>
      </svg>
    </div>
  );
};
