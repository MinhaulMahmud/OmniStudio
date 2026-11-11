import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { GearWheel } from "./GearWheel";

export interface SequentialGearboxMechanismProps {
  currentGear?: number; // 1 to 6 (or 0 for Neutral)
  inputRpm?: number;
  width?: number;
  height?: number;
  showTorquePath?: boolean;
}

export const SequentialGearboxMechanism: React.FC<SequentialGearboxMechanismProps> = ({
  currentGear,
  inputRpm = 6000,
  width = 1100,
  height = 550,
  showTorquePath = true,
}) => {
  const frame = useCurrentFrame();

  // If gear is not explicitly provided, cycle through gears over time
  // Frame cycle: 0-100 (1st), 100-200 (2nd), 200-300 (3rd), 300-400 (4th), 400-500 (5th), 500-600 (6th)
  const activeGear = currentGear !== undefined ? currentGear : (Math.floor(frame / 90) % 6) + 1;

  // Real Motorcycle 6-Speed Gear Ratios (Teeth counts: Drive / Driven)
  const gearSpecs = [
    { gear: 1, driveTeeth: 13, drivenTeeth: 37, driveR: 32, drivenR: 82, ratio: 2.85, label: "1st Gear (Torque)" },
    { gear: 2, driveTeeth: 17, drivenTeeth: 32, driveR: 40, drivenR: 74, ratio: 1.88, label: "2nd Gear" },
    { gear: 3, driveTeeth: 20, drivenTeeth: 28, driveR: 47, drivenR: 67, ratio: 1.40, label: "3rd Gear" },
    { gear: 4, driveTeeth: 22, drivenTeeth: 25, driveR: 52, drivenR: 62, ratio: 1.14, label: "4th Gear" },
    { gear: 5, driveTeeth: 24, drivenTeeth: 23, driveR: 57, drivenR: 57, ratio: 0.96, label: "5th Gear (Direct)" },
    { gear: 6, driveTeeth: 26, drivenTeeth: 21, driveR: 62, drivenR: 52, ratio: 0.81, label: "6th Gear (Overdrive)" },
  ];

  const currentSpec = gearSpecs[activeGear - 1] || gearSpecs[0];

  // Base rotation speed (degrees per frame)
  const baseSpeed = 4.0;
  const inputRotation = frame * baseSpeed;
  const outputRotation = -inputRotation / currentSpec.ratio;

  // Horizontal spacing between gear pairs
  const startX = 140;
  const gearSpacing = 150;
  const inputShaftY = 170;
  const outputShaftY = 320;

  // Calculate dog clutch lateral position (slides towards active gear)
  const dogClutchX = startX + (activeGear - 1) * gearSpacing;

  // Output RPM and Torque Multiplier
  const outputRpm = Math.round(inputRpm / currentSpec.ratio);
  const torqueMultiplier = ((currentSpec.ratio - 1) * 100).toFixed(0);

  return (
    <div
      style={{
        width: `${width}px`,
        height: `${height}px`,
        position: "relative",
        backgroundColor: "#070b14",
        borderRadius: "24px",
        border: "1px solid rgba(56, 189, 248, 0.25)",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)",
        overflow: "hidden",
        fontFamily: "'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Background blueprint grid */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage:
            "linear-gradient(rgba(56, 189, 248, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.04) 1px, transparent 1px)",
          backgroundSize: "30px 30px",
          pointerEvents: "none",
        }}
      />

      {/* Header Telemetry Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "18px 30px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          backgroundColor: "rgba(15, 23, 42, 0.7)",
          backdropFilter: "blur(8px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span
            style={{
              padding: "4px 12px",
              borderRadius: "8px",
              backgroundColor: "#0284c7",
              color: "#ffffff",
              fontSize: "13px",
              fontWeight: 800,
              letterSpacing: "1px",
            }}
          >
            CONSTANT MESH
          </span>
          <span style={{ color: "#38bdf8", fontWeight: 700, fontSize: "18px" }}>
            6-Speed Sequential Motorcycle Transmission
          </span>
        </div>

        {/* Active Gear Indicator Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              fontSize: "24px",
              fontWeight: 900,
              color: "#38bdf8",
              backgroundColor: "rgba(56, 189, 248, 0.15)",
              border: "1px solid #38bdf8",
              borderRadius: "12px",
              padding: "4px 18px",
              boxShadow: "0 0 15px rgba(56, 189, 248, 0.4)",
            }}
          >
            GEAR {activeGear}
          </div>
          <div style={{ fontSize: "14px", color: "#94a3b8" }}>
            Ratio: <strong style={{ color: "#ffffff" }}>{currentSpec.ratio}:1</strong>
          </div>
        </div>
      </div>

      {/* Main SVG Mechanical Viewport */}
      <svg
        viewBox={`0 0 ${width} ${height - 70}`}
        style={{ width: "100%", height: `${height - 70}px` }}
      >
        <defs>
          {/* Torque energy gradient */}
          <linearGradient id="torqueGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>

          {/* Shaft metal gradient */}
          <linearGradient id="shaftGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#64748b" />
            <stop offset="50%" stopColor="#cbd5e1" />
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>
        </defs>

        {/* ─── 1. SHAFTS & BEARINGS ─────────────────────────────────────── */}
        {/* Input Shaft (Mainshaft) */}
        <rect
          x={40}
          y={inputShaftY - 10}
          width={width - 120}
          height={20}
          rx={4}
          fill="url(#shaftGrad)"
          stroke="#0f172a"
          strokeWidth="1.5"
        />
        {/* Input Shaft Label */}
        <text
          x={50}
          y={inputShaftY - 18}
          fill="#38bdf8"
          fontSize="13"
          fontWeight="700"
          letterSpacing="1px"
        >
          INPUT SHAFT (From Clutch) ➜
        </text>

        {/* Output Shaft (Countershaft) */}
        <rect
          x={40}
          y={outputShaftY - 12}
          width={width - 120}
          height={24}
          rx={5}
          fill="url(#shaftGrad)"
          stroke="#0f172a"
          strokeWidth="1.5"
        />
        {/* Output Shaft Label */}
        <text
          x={50}
          y={outputShaftY + 36}
          fill="#a855f7"
          fontSize="13"
          fontWeight="700"
          letterSpacing="1px"
        >
          OUTPUT SHAFT (To Drive Sprocket) ➜
        </text>

        {/* Drive Sprocket at end of output shaft */}
        <g transform={`translate(${width - 70}, ${outputShaftY})`}>
          <circle r={32} fill="#1e293b" stroke="#a855f7" strokeWidth="3" />
          {[...Array(14)].map((_, idx) => (
            <rect
              key={idx}
              x={-4}
              y={-36}
              width={8}
              height={8}
              fill="#a855f7"
              transform={`rotate(${(idx * 360) / 14 + outputRotation})`}
            />
          ))}
          <text y={48} textAnchor="middle" fill="#a855f7" fontSize="11" fontWeight="700">
            DRIVE SPROCKET
          </text>
        </g>

        {/* ─── 2. ALL 6 CONSTANT MESH GEAR PAIRS ──────────────────────── */}
        {gearSpecs.map((spec) => {
          const pairX = startX + (spec.gear - 1) * gearSpacing;
          const isSelected = spec.gear === activeGear;

          // Free-wheeling gears spin independently unless engaged by dog clutch
          const gearInputRot = inputRotation;
          const gearOutputRot = isSelected ? outputRotation : -inputRotation / spec.ratio;

          return (
            <g key={spec.gear}>
              {/* Vertical Meshing Alignment Line */}
              <line
                x1={pairX}
                y1={inputShaftY}
                x2={pairX}
                y2={outputShaftY}
                stroke={isSelected ? "#38bdf8" : "rgba(255,255,255,0.06)"}
                strokeWidth={isSelected ? "2" : "1"}
                strokeDasharray={isSelected ? "4 2" : "2 4"}
              />

              {/* Upper Gear (Drive Gear on Mainshaft) */}
              <GearWheel
                teeth={spec.driveTeeth}
                radius={spec.driveR}
                rotation={gearInputRot}
                x={pairX}
                y={inputShaftY}
                isEngaged={isSelected}
                accentColor="#38bdf8"
                hasDogs={spec.gear % 2 === 1}
                label={`${spec.driveTeeth}T`}
              />

              {/* Lower Gear (Driven Gear on Countershaft) */}
              <GearWheel
                teeth={spec.drivenTeeth}
                radius={spec.drivenR}
                rotation={gearOutputRot}
                x={pairX}
                y={outputShaftY}
                isEngaged={isSelected}
                accentColor="#a855f7"
                hasDogs={spec.gear % 2 === 0}
                label={`${spec.drivenTeeth}T`}
              />

              {/* Gear Name Tag */}
              <text
                x={pairX}
                y={inputShaftY - 70}
                textAnchor="middle"
                fill={isSelected ? "#38bdf8" : "#64748b"}
                fontSize="13"
                fontWeight={isSelected ? "800" : "500"}
              >
                {spec.label}
              </text>
            </g>
          );
        })}

        {/* ─── 3. DOG CLUTCH & SHIFT FORK MECHANISM ─────────────────────── */}
        {/* Sliding Dog Ring Collar */}
        <g transform={`translate(${dogClutchX}, ${outputShaftY})`}>
          {/* Dog Ring Body sliding on splines */}
          <rect
            x={-18}
            y={-22}
            width={36}
            height={44}
            rx={4}
            fill="#f59e0b"
            stroke="#fbbf24"
            strokeWidth="2.5"
            filter="drop-shadow(0 0 10px rgba(245, 158, 11, 0.6))"
          />
          {/* Locking Dogs (Lug protrusions) */}
          <rect x={-26} y={-14} width={8} height={28} rx={2} fill="#f59e0b" stroke="#fbbf24" />
          <rect x={18} y={-14} width={8} height={28} rx={2} fill="#f59e0b" stroke="#fbbf24" />

          {/* Shift Fork Arm engaging the groove in dog ring */}
          <path
            d="M -12,22 L -12,45 L 12,45 L 12,22 Z"
            fill="#d97706"
            stroke="#f59e0b"
            strokeWidth="1.5"
          />
          <text y={62} textAnchor="middle" fill="#fbbf24" fontSize="11" fontWeight="700">
            SHIFT FORK
          </text>
        </g>

        {/* ─── 4. ANIMATED TORQUE PATH ─────────────────────────────────── */}
        {showTorquePath && (
          <g>
            {/* Pulsing energy path through engaged gear pair */}
            <path
              d={`M 40,${inputShaftY} L ${dogClutchX},${inputShaftY} L ${dogClutchX},${outputShaftY} L ${width - 70},${outputShaftY}`}
              fill="none"
              stroke="url(#torqueGlow)"
              strokeWidth="5"
              strokeLinecap="round"
              strokeDasharray="16 10"
              strokeDashoffset={-frame * 6}
              opacity="0.9"
              filter="drop-shadow(0 0 12px #38bdf8)"
            />

            {/* Torque Flow Indicator Label */}
            <g transform={`translate(${dogClutchX + 30}, ${(inputShaftY + outputShaftY) / 2})`}>
              <rect x={0} y={-14} width={120} height={28} rx={6} fill="#0f172a" stroke="#f59e0b" strokeWidth="1.5" />
              <text x={60} y={4} textAnchor="middle" fill="#fbbf24" fontSize="12" fontWeight="700">
                TORQUE FLOW
              </text>
            </g>
          </g>
        )}
      </svg>

      {/* Footer Metrics & Gauges */}
      <div
        style={{
          position: "absolute",
          bottom: "12px",
          left: "24px",
          right: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 20px",
          backgroundColor: "rgba(15, 23, 42, 0.8)",
          borderRadius: "14px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        <div style={{ display: "flex", gap: "30px" }}>
          <div>
            <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Engine Crank RPM</div>
            <div style={{ fontSize: "18px", fontWeight: 800, color: "#38bdf8" }}>{inputRpm.toLocaleString()} RPM</div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Output Sprocket RPM</div>
            <div style={{ fontSize: "18px", fontWeight: 800, color: "#a855f7" }}>{outputRpm.toLocaleString()} RPM</div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>Torque Multiplier</div>
            <div style={{ fontSize: "18px", fontWeight: 800, color: currentSpec.ratio >= 1.0 ? "#22c55e" : "#f59e0b" }}>
              {currentSpec.ratio >= 1.0 ? `+${torqueMultiplier}%` : `${torqueMultiplier}% (Overdrive)`}
            </div>
          </div>
        </div>

        {/* Shift Pattern Legend */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "12px", color: "#94a3b8" }}>Motorcycle Shift Drum:</span>
          {["1", "N", "2", "3", "4", "5", "6"].map((g, i) => {
            const isCur = (g === "N" && activeGear === 0) || g === String(activeGear);
            return (
              <span
                key={i}
                style={{
                  padding: "2px 8px",
                  borderRadius: "6px",
                  backgroundColor: isCur ? "#38bdf8" : "rgba(255,255,255,0.05)",
                  color: isCur ? "#000000" : "#94a3b8",
                  fontWeight: isCur ? 900 : 500,
                  fontSize: "13px",
                }}
              >
                {g}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};
