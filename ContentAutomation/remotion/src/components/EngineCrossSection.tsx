import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export interface EngineCrossSectionProps {
  crankAngle?: number; // degrees
  scale?: number;
  highlightTransmission?: boolean;
  opacity?: number;
  x?: number;
  y?: number;
}

export const EngineCrossSection: React.FC<EngineCrossSectionProps> = ({
  crankAngle,
  scale = 1.0,
  highlightTransmission = false,
  opacity = 1.0,
  x = 0,
  y = 0,
}) => {
  const frame = useCurrentFrame();

  // If crankAngle is not explicitly provided, calculate continuous rotation
  const theta = (crankAngle !== undefined ? crankAngle : frame * 6) % 360;
  const thetaRad = (theta * Math.PI) / 180;

  // Mechanical Geometry Constants (in SVG coordinate space)
  const crankRadius = 45; // Crank throw (half of stroke)
  const rodLength = 140; // Connecting rod length
  const crankCenterY = 240; // Y position of crankshaft axis
  const crankCenterX = 180; // X position of crankshaft axis

  // Crankpin coordinates (revolving circle)
  const pinX = crankCenterX + Math.sin(thetaRad) * crankRadius;
  const pinY = crankCenterY - Math.cos(thetaRad) * crankRadius;

  // Piston wrist-pin Y coordinate via slider-crank kinematic equation:
  // y = crankCenterY - (r * cos(theta) + sqrt(l^2 - (r * sin(theta))^2))
  const rodSideOffset = Math.sin(thetaRad) * crankRadius;
  const pistonWristY = crankCenterY - (Math.cos(thetaRad) * crankRadius + Math.sqrt(rodLength * rodLength - rodSideOffset * rodSideOffset));
  const pistonWristX = crankCenterX;

  // Combustion Flash when piston is near Top Dead Center (theta between 350 and 15 deg)
  const isNearTDC = theta > 348 || theta < 18;
  const sparkIntensity = isNearTDC ? 1.0 : 0.0;

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <defs>
        {/* Combustion Gradient */}
        <radialGradient id="combustionGlow" cx="50%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#ffedd5" stopOpacity="1" />
          <stop offset="30%" stopColor="#f97316" stopOpacity="0.8" />
          <stop offset="70%" stopColor="#ef4444" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#7f1d1d" stopOpacity="0" />
        </radialGradient>

        {/* Metal Casing Gradient */}
        <linearGradient id="metalCase" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#334155" />
          <stop offset="50%" stopColor="#1e293b" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>

        {/* Cylinder Bore Gradient */}
        <linearGradient id="cylinderWall" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1e293b" />
          <stop offset="15%" stopColor="#475569" />
          <stop offset="85%" stopColor="#475569" />
          <stop offset="100%" stopColor="#1e293b" />
        </linearGradient>
      </defs>

      {/* ─── 1. OUTER ENGINE CASING & CYLINDER ──────────────────────────── */}
      {/* Cylinder Cooling Fins */}
      {[-30, -5, 20, 45, 70].map((finY, i) => (
        <rect
          key={i}
          x={100}
          y={finY}
          width={160}
          height={8}
          rx={4}
          fill="#334155"
          stroke="#475569"
          strokeWidth="1.5"
        />
      ))}

      {/* Cylinder Block Outline */}
      <path
        d="M 125,-40 L 235,-40 L 235,140 L 280,180 L 390,180 L 400,280 L 360,330 L 120,330 L 100,250 L 125,140 Z"
        fill="url(#metalCase)"
        stroke="#64748b"
        strokeWidth="3"
      />

      {/* Cylinder Bore Wall (Inner Chamber) */}
      <rect
        x={130}
        y={-25}
        width={100}
        height={160}
        fill="url(#cylinderWall)"
        stroke="#334155"
        strokeWidth="2"
      />

      {/* Combustion Flash inside cylinder head */}
      {isNearTDC && (
        <rect
          x={130}
          y={-25}
          width={100}
          height={Math.max(20, pistonWristY - 35 - (-25))}
          fill="url(#combustionGlow)"
          filter="blur(3px)"
        />
      )}

      {/* Spark Plug at Cylinder Head */}
      <rect x={175} y={-55} width={10} height={20} fill="#e2e8f0" stroke="#0f172a" />
      <circle cx={180} cy={-25} r={sparkIntensity * 10} fill="#fef08a" opacity={sparkIntensity} />

      {/* ─── 2. RECIPROCATING PISTON ───────────────────────────────────── */}
      {/* Piston Body (Moves vertically along wrist-pin Y) */}
      <g transform={`translate(${pistonWristX - 48}, ${pistonWristY - 35})`}>
        {/* Piston Crown & Skirt */}
        <path
          d="M 4,0 L 92,0 Q 96,0 96,6 L 96,48 Q 96,52 90,52 L 72,52 L 72,38 L 24,38 L 24,52 L 6,52 Q 0,52 0,46 L 0,6 Q 0,0 4,0 Z"
          fill="#94a3b8"
          stroke="#cbd5e1"
          strokeWidth="2"
        />
        {/* Piston Rings Grooves */}
        <line x1={0} y1={8} x2={96} y2={8} stroke="#0f172a" strokeWidth="2" />
        <line x1={0} y1={16} x2={96} y2={16} stroke="#0f172a" strokeWidth="2" />
        <line x1={0} y1={24} x2={96} y2={24} stroke="#0f172a" strokeWidth="2" />

        {/* Wrist Pin */}
        <circle cx={48} cy={35} r={9} fill="#475569" stroke="#e2e8f0" strokeWidth="2" />
      </g>

      {/* ─── 3. ARTICULATING CONNECTING ROD ────────────────────────────── */}
      <g>
        {/* Rod Stem */}
        <line
          x1={pistonWristX}
          y1={pistonWristY}
          x2={pinX}
          y2={pinY}
          stroke="#cbd5e1"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <line
          x1={pistonWristX}
          y1={pistonWristY}
          x2={pinX}
          y2={pinY}
          stroke="#64748b"
          strokeWidth="6"
          strokeLinecap="round"
        />

        {/* Small End Bearing (Wrist Pin) */}
        <circle cx={pistonWristX} cy={pistonWristY} r={12} fill="#64748b" stroke="#e2e8f0" strokeWidth="2" />

        {/* Big End Bearing (Crank Pin) */}
        <circle cx={pinX} cy={pinY} r={18} fill="#475569" stroke="#e2e8f0" strokeWidth="2.5" />
      </g>

      {/* ─── 4. REVOLVING CRANKSHAFT & COUNTERWEIGHT ───────────────────── */}
      <g transform={`translate(${crankCenterX}, ${crankCenterY}) rotate(${theta})`}>
        {/* Crank Counterweight Lobes */}
        <path
          d={`M -45,0 A 55,55 0 0,0 45,0 L 25,-25 L -25,-25 Z`}
          fill="#475569"
          stroke="#94a3b8"
          strokeWidth="2"
        />
        {/* Main Crankshaft Center Pivot */}
        <circle cx={0} cy={0} r={22} fill="#1e293b" stroke="#38bdf8" strokeWidth="3" />
        <circle cx={0} cy={0} r={8} fill="#38bdf8" />

        {/* Crankpin Offset Circle */}
        <circle cx={0} cy={-crankRadius} r={14} fill="#e2e8f0" stroke="#0f172a" strokeWidth="2" />
      </g>

      {/* ─── 5. TRANSMISSION COMPARTMENT (GEARBOX LOCATION) ────────────── */}
      {/* Gearbox Cavity in lower rear of crankcase */}
      <g>
        <rect
          x={250}
          y={195}
          width={130}
          height={115}
          rx={16}
          fill={highlightTransmission ? "rgba(56, 189, 248, 0.15)" : "#0f172a"}
          stroke={highlightTransmission ? "#38bdf8" : "#475569"}
          strokeWidth={highlightTransmission ? "3" : "1.5"}
          strokeDasharray={highlightTransmission ? "6 4" : "none"}
        />

        {/* Input Shaft (Mainshaft) representation */}
        <circle
          cx={285}
          cy={245}
          r={28}
          fill="none"
          stroke={highlightTransmission ? "#38bdf8" : "#64748b"}
          strokeWidth="2"
          strokeDasharray="4 3"
        />
        <circle cx={285} cy={245} r={8} fill={highlightTransmission ? "#38bdf8" : "#94a3b8"} />

        {/* Output Shaft (Countershaft) representation */}
        <circle
          cx={345}
          cy={255}
          r={36}
          fill="none"
          stroke={highlightTransmission ? "#a855f7" : "#64748b"}
          strokeWidth="2"
          strokeDasharray="4 3"
        />
        <circle cx={345} cy={255} r={10} fill={highlightTransmission ? "#a855f7" : "#94a3b8"} />

        {/* Meshing Contact Indicator */}
        {highlightTransmission && (
          <circle
            cx={315}
            cy={250}
            r={5}
            fill="#f59e0b"
            filter="drop-shadow(0 0 6px #f59e0b)"
          />
        )}
      </g>

      {/* ─── 6. TECHNICAL ANNOTATIONS & POINTERS ───────────────────────── */}
      {/* Crankcase Label */}
      <text x={180} y={315} textAnchor="middle" fill="#64748b" fontSize="11" fontWeight="600" letterSpacing="1px">
        CRANKCASE / FLYWHEEL
      </text>

      {/* Gearbox Position Callout */}
      {highlightTransmission && (
        <g>
          {/* Animated Target Reticle */}
          <circle
            cx={315}
            cy={250}
            r={50}
            fill="none"
            stroke="#38bdf8"
            strokeWidth="1.5"
            opacity={interpolate(Math.sin(frame / 8), [-1, 1], [0.4, 0.9])}
          />
          <line x1={315} y1={185} x2={315} y2={195} stroke="#38bdf8" strokeWidth="2" />
          <line x1={315} y1={305} x2={315} y2={315} stroke="#38bdf8" strokeWidth="2" />
          <line x1={240} y1={250} x2={250} y2={250} stroke="#38bdf8" strokeWidth="2" />
          <line x1={380} y1={250} x2={390} y2={250} stroke="#38bdf8" strokeWidth="2" />

          {/* Pointer Badge */}
          <g transform="translate(240, 140)">
            <rect x={0} y={0} width={150} height={32} rx={8} fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
            <text x={75} y={20} textAnchor="middle" fill="#ffffff" fontSize="12" fontWeight="700" letterSpacing="0.5px">
              GEARBOX CHAMBER
            </text>
          </g>
          <line x1={315} y1={172} x2={315} y2={195} stroke="#38bdf8" strokeWidth="2" strokeDasharray="3 3" />
        </g>
      )}
    </g>
  );
};
