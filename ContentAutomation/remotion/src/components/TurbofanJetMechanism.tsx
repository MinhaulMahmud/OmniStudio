import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export interface TurbofanJetMechanismProps {
  width?: number;
  height?: number;
  stage?: number; // 0: Intake & Bypass, 1: Compression, 2: Combustion, 3: Expansion & Thrust
  rpm?: number;
}

export const TurbofanJetMechanism: React.FC<TurbofanJetMechanismProps> = ({
  width = 680,
  height = 440,
  stage = 0,
  rpm = 3600,
}) => {
  const frame = useCurrentFrame();

  // Rotation angles for fan and turbine spools
  const fanAngle = (frame * 12) % 360;
  const hpSpoolAngle = (frame * 24) % 360;

  // Flame fluctuation for combustion chamber
  const flamePulse = interpolate(Math.sin(frame / 2), [-1, 1], [0.85, 1.15]);
  const exhaustGlow = interpolate(Math.sin(frame / 3), [-1, 1], [0.75, 1.0]);

  // Traveling airflow particles from intake to exhaust
  const particleOffset = (frame * 8) % 100;

  return (
    <div
      style={{
        width: `${width}px`,
        height: `${height}px`,
        backgroundColor: "#050713",
        borderRadius: "20px",
        border: "1px solid rgba(0, 229, 255, 0.35)",
        overflow: "hidden",
        position: "relative",
        boxShadow: "0 15px 35px rgba(0,0,0,0.7), 0 0 25px rgba(0, 229, 255, 0.15)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top HUD Telemetry Status Bar */}
      <div
        style={{
          padding: "10px 18px",
          backgroundColor: "rgba(10, 18, 36, 0.85)",
          borderBottom: "1px solid rgba(0, 229, 255, 0.2)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "11px",
          fontWeight: 800,
          letterSpacing: "1px",
          color: "#00e5ff",
          textTransform: "uppercase",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "#22c55e",
              boxShadow: "0 0 10px #22c55e",
            }}
          />
          <span>HIGH-BYPASS TURBOFAN PROPULSION KINEMATICS</span>
        </div>
        <div style={{ display: "flex", gap: "16px", color: "rgba(255,255,255,0.7)" }}>
          <span>FAN: <strong style={{ color: "#38bdf8" }}>{rpm} RPM</strong></span>
          <span>COMPRESSION: <strong style={{ color: "#a855f7" }}>42:1</strong></span>
          <span>T_MAX: <strong style={{ color: "#f97316" }}>1,750°C</strong></span>
          <span>THRUST: <strong style={{ color: "#22c55e" }}>82,500 LBF</strong></span>
        </div>
      </div>

      {/* Main Vector Jet Cutaway SVG */}
      <svg
        viewBox="0 0 800 420"
        style={{
          width: "100%",
          height: "calc(100% - 38px)",
          flex: 1,
        }}
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="nacelleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#1e293b" />
            <stop offset="40%" stopColor="#334155" />
            <stop offset="60%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>

          <linearGradient id="coreCasingGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
            <stop offset="50%" stopColor="#818cf8" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.5" />
          </linearGradient>

          <linearGradient id="combustionFlameGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#fef08a" />
            <stop offset="30%" stopColor="#f97316" />
            <stop offset="70%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.8" />
          </linearGradient>

          <radialGradient id="nozzlePlumeGrad" cx="0%" cy="50%" r="100%">
            <stop offset="0%" stopColor="#67e8f9" stopOpacity="0.95" />
            <stop offset="25%" stopColor="#38bdf8" stopOpacity="0.8" />
            <stop offset="60%" stopColor="#818cf8" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#050713" stopOpacity="0" />
          </radialGradient>

          {/* Mach Shock Diamonds Pattern */}
          <linearGradient id="machDiamond" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.2" />
          </linearGradient>
        </defs>

        {/* ─── 1. INCOMING AIRFLOW STREAMLINES (LEFT SIDE) ────────────────── */}
        {[80, 120, 160, 200, 240, 280, 320].map((y, idx) => {
          const travelX = (particleOffset * 2.5 + idx * 25) % 180;
          return (
            <g key={`inflow-${idx}`}>
              <line
                x1={20}
                y1={y}
                x2={140}
                y2={y}
                stroke="#00e5ff"
                strokeWidth="1.2"
                strokeDasharray="8 6"
                strokeOpacity="0.35"
              />
              <circle cx={20 + travelX} cy={y} r="2" fill="#00e5ff" opacity="0.8" />
            </g>
          );
        })}

        {/* ─── 2. OUTER ENGINE NACELLE & COWLING (CUTAWAY) ──────────────── */}
        {/* Top Nacelle Half */}
        <path
          d="M 120,40 C 100,40 85,55 85,75 L 140,75 C 240,75 360,65 520,95 L 530,120 L 480,120 C 350,90 230,105 150,110 Z"
          fill="url(#nacelleGradient)"
          stroke="#475569"
          strokeWidth="2"
        />
        {/* Bottom Nacelle Half */}
        <path
          d="M 120,360 C 100,360 85,345 85,325 L 140,325 C 240,325 360,335 520,305 L 530,280 L 480,280 C 350,310 230,295 150,290 Z"
          fill="url(#nacelleGradient)"
          stroke="#475569"
          strokeWidth="2"
        />

        {/* High-Bypass Duct Air Channel Indicator */}
        <path
          d="M 160,115 C 260,115 360,105 480,125"
          fill="none"
          stroke="#00e5ff"
          strokeWidth="2"
          strokeDasharray="6 4"
          strokeOpacity="0.5"
        />
        <path
          d="M 160,285 C 260,285 360,295 480,275"
          fill="none"
          stroke="#00e5ff"
          strokeWidth="2"
          strokeDasharray="6 4"
          strokeOpacity="0.5"
        />

        {/* ─── 3. ENGINE CORE CASING ────────────────────────────────────── */}
        <path
          d="M 200,140 L 340,140 L 430,150 L 520,165 L 580,185 L 580,215 L 520,235 L 430,250 L 340,260 L 200,260 Z"
          fill="#0a0f1d"
          stroke="url(#coreCasingGradient)"
          strokeWidth="2.5"
        />

        {/* ─── 4. ROTATING FRONT BYPASS FAN (TITANIUM BLADES) ──────────── */}
        {/* Fan Spinner Cone */}
        <path
          d="M 100,200 L 150,160 L 150,240 Z"
          fill="#38bdf8"
          stroke="#ffffff"
          strokeWidth="2"
        />

        {/* Fan Blades (Left-hand intake) */}
        {[-80, -60, -40, -20, 0, 20, 40, 60, 80].map((offsetY, i) => {
          const bladeAngle = (fanAngle + i * 40) % 360;
          const bladeWidth = Math.abs(Math.sin((bladeAngle * Math.PI) / 180)) * 14 + 4;
          return (
            <rect
              key={`fan-${i}`}
              x={145}
              y={200 + offsetY - 14}
              width={bladeWidth}
              height={28}
              rx={3}
              fill="#94a3b8"
              stroke="#00e5ff"
              strokeWidth="1.2"
              opacity="0.9"
            />
          );
        })}

        {/* ─── 5. MULTI-STAGE AXIAL COMPRESSOR (STAGES 1-5) ────────────── */}
        {[0, 1, 2, 3].map((stg) => {
          const compX = 220 + stg * 28;
          const compH = 90 - stg * 10;
          return (
            <g key={`comp-${stg}`}>
              {/* Rotor Blades */}
              <rect
                x={compX}
                y={200 - compH / 2}
                width={8}
                height={compH}
                rx={2}
                fill="#38bdf8"
                stroke="#0284c7"
                strokeWidth="1"
              />
              {/* Stator Vane */}
              <rect
                x={compX + 14}
                y={200 - compH / 2}
                width={5}
                height={compH}
                rx={1}
                fill="#64748b"
                opacity="0.8"
              />
            </g>
          );
        })}

        {/* ─── 6. ANNULAR COMBUSTION CHAMBER (FIRE IGNITION) ───────────── */}
        <g transform={`scale(${flamePulse}) translate(${340 * (1 - flamePulse)}, ${200 * (1 - flamePulse)})`}>
          {/* Upper Flame Cavity */}
          <path
            d="M 345,155 Q 390,145 425,160 Q 385,175 345,165 Z"
            fill="url(#combustionFlameGrad)"
            opacity="0.95"
            filter="drop-shadow(0 0 10px #f97316)"
          />
          {/* Lower Flame Cavity */}
          <path
            d="M 345,245 Q 390,255 425,240 Q 385,225 345,235 Z"
            fill="url(#combustionFlameGrad)"
            opacity="0.95"
            filter="drop-shadow(0 0 10px #f97316)"
          />
        </g>

        {/* Fuel Injectors */}
        <circle cx={345} cy={160} r="4" fill="#ffffff" stroke="#ef4444" strokeWidth="2" />
        <circle cx={345} cy={240} r="4" fill="#ffffff" stroke="#ef4444" strokeWidth="2" />

        {/* ─── 7. HIGH & LOW PRESSURE TURBINE STAGES ───────────────────── */}
        {[0, 1].map((tIdx) => {
          const turbX = 445 + tIdx * 25;
          const turbH = 65 + tIdx * 12;
          return (
            <g key={`turb-${tIdx}`}>
              <rect
                x={turbX}
                y={200 - turbH / 2}
                width={8}
                height={turbH}
                rx={2}
                fill="#f59e0b"
                stroke="#d97706"
                strokeWidth="1"
              />
            </g>
          );
        })}

        {/* Central Drive Shaft Spool */}
        <rect x={145} y={196} width={340} height={8} fill="#94a3b8" stroke="#334155" strokeWidth="1" />

        {/* ─── 8. CONVERGENT EXHAUST NOZZLE & MACH SHOCK PLUME ─────────── */}
        {/* Exhaust Centerbody Tailcone */}
        <path d="M 500,185 L 600,200 L 500,215 Z" fill="#475569" stroke="#64748b" strokeWidth="1.5" />

        {/* Blazing Supersonic Thrust Plume */}
        <g opacity={exhaustGlow}>
          <path
            d="M 580,185 Q 680,170 780,150 Q 750,200 780,250 Q 680,230 580,215 Z"
            fill="url(#nozzlePlumeGrad)"
          />
          {/* Mach Shock Diamonds */}
          {[620, 660, 700, 740].map((dx, i) => (
            <polygon
              key={`diamond-${i}`}
              points={`${dx},200 ${dx + 15},192 ${dx + 30},200 ${dx + 15},208`}
              fill="url(#machDiamond)"
            />
          ))}
        </g>

        {/* ─── 9. TECHNICAL ANNOTATION CALLOUTS ────────────────────────── */}
        <g style={{ fontSize: "10px", fontWeight: 700, fill: "rgba(255,255,255,0.7)" }}>
          {/* Stage Labels */}
          <text x={140} y={385} fill="#00e5ff">1. INTAKE FAN</text>
          <text x={240} y={385} fill="#38bdf8">2. COMPRESSOR</text>
          <text x={350} y={385} fill="#f97316">3. COMBUSTOR</text>
          <text x={450} y={385} fill="#eab308">4. TURBINE</text>
          <text x={620} y={385} fill="#22c55e">5. THRUST NOZZLE</text>

          {/* Connective Guide Lines */}
          <line x1={140} y1={368} x2={140} y2={350} stroke="#00e5ff" strokeWidth="1" strokeDasharray="2 2" />
          <line x1={270} y1={368} x2={270} y2={280} stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" />
          <line x1={385} y1={368} x2={385} y2={265} stroke="#f97316" strokeWidth="1" strokeDasharray="2 2" />
          <line x1={465} y1={368} x2={465} y2={255} stroke="#eab308" strokeWidth="1" strokeDasharray="2 2" />
          <line x1={650} y1={368} x2={650} y2={240} stroke="#22c55e" strokeWidth="1" strokeDasharray="2 2" />
        </g>
      </svg>
    </div>
  );
};
