import React from "react";

export interface GearWheelProps {
  teeth: number;
  radius: number;
  rotation: number; // degrees
  x?: number;
  y?: number;
  color?: string;
  accentColor?: string;
  isEngaged?: boolean;
  hasDogs?: boolean;
  boreRadius?: number;
  label?: string;
}

export const GearWheel: React.FC<GearWheelProps> = ({
  teeth,
  radius,
  rotation,
  x = 0,
  y = 0,
  color = "#475569",
  accentColor = "#38bdf8",
  isEngaged = false,
  hasDogs = false,
  boreRadius = 18,
  label,
}) => {
  // Generate SVG path for an involute gear wheel
  const toothDepth = radius * 0.16;
  const innerRadius = radius - toothDepth;
  const outerRadius = radius + toothDepth * 0.6;
  const step = (Math.PI * 2) / teeth;

  const points: string[] = [];
  for (let i = 0; i < teeth; i++) {
    const angle0 = i * step;
    const angle1 = angle0 + step * 0.25;
    const angle2 = angle0 + step * 0.45;
    const angle3 = angle0 + step * 0.75;
    const angle4 = angle0 + step;

    // Root -> Dedendum -> Addendum tooth profile
    const x0 = Math.cos(angle0) * innerRadius;
    const y0 = Math.sin(angle0) * innerRadius;
    const x1 = Math.cos(angle1) * outerRadius;
    const y1 = Math.sin(angle1) * outerRadius;
    const x2 = Math.cos(angle2) * outerRadius;
    const y2 = Math.sin(angle2) * outerRadius;
    const x3 = Math.cos(angle3) * innerRadius;
    const y3 = Math.sin(angle3) * innerRadius;
    const x4 = Math.cos(angle4) * innerRadius;
    const y4 = Math.sin(angle4) * innerRadius;

    if (i === 0) {
      points.push(`M ${x0} ${y0}`);
    } else {
      points.push(`L ${x0} ${y0}`);
    }
    points.push(`L ${x1} ${y1}`);
    points.push(`L ${x2} ${y2}`);
    points.push(`L ${x3} ${y3}`);
    points.push(`L ${x4} ${y4}`);
  }
  const gearPath = points.join(" ") + " Z";

  return (
    <g transform={`translate(${x}, ${y})`}>
      {/* Outer Glow when engaged */}
      {isEngaged && (
        <circle
          r={outerRadius + 8}
          fill="none"
          stroke={accentColor}
          strokeWidth="4"
          opacity="0.4"
          filter="blur(6px)"
        />
      )}

      {/* Rotating Gear Body */}
      <g transform={`rotate(${rotation})`}>
        {/* Main Toothed Gear Body */}
        <path
          d={gearPath}
          fill={isEngaged ? "#1e293b" : color}
          stroke={isEngaged ? accentColor : "#94a3b8"}
          strokeWidth={isEngaged ? "3" : "2"}
          style={{
            filter: isEngaged ? `drop-shadow(0 0 12px ${accentColor}88)` : "none",
            transition: "fill 0.2s, stroke 0.2s",
          }}
        />

        {/* Pitch Circle indicator */}
        <circle
          r={radius}
          fill="none"
          stroke={isEngaged ? accentColor : "rgba(255,255,255,0.15)"}
          strokeWidth="1"
          strokeDasharray="4 3"
        />

        {/* Lightweighting Cutouts */}
        {[...Array(4)].map((_, idx) => {
          const cutAngle = (idx * Math.PI) / 2;
          const dist = (radius + boreRadius) / 2;
          const cx = Math.cos(cutAngle) * dist;
          const cy = Math.sin(cutAngle) * dist;
          return (
            <circle
              key={idx}
              cx={cx}
              cy={cy}
              r={radius * 0.18}
              fill="#0b0f19"
              stroke={isEngaged ? accentColor : "rgba(255,255,255,0.2)"}
              strokeWidth="1.5"
            />
          );
        })}

        {/* Center Shaft Bore */}
        <circle
          r={boreRadius}
          fill="#0f172a"
          stroke={isEngaged ? accentColor : "#64748b"}
          strokeWidth="2.5"
        />

        {/* Dog Clutch Pockets / Dogs if specified */}
        {hasDogs && (
          <>
            {[...Array(3)].map((_, idx) => {
              const a = (idx * Math.PI * 2) / 3;
              const r = boreRadius + 14;
              return (
                <rect
                  key={idx}
                  x={Math.cos(a) * r - 5}
                  y={Math.sin(a) * r - 5}
                  width="10"
                  height="10"
                  rx="2"
                  fill={isEngaged ? "#f59e0b" : "#475569"}
                  stroke={isEngaged ? "#fbbf24" : "#94a3b8"}
                  strokeWidth="1.5"
                />
              );
            })}
          </>
        )}
      </g>

      {/* Static Center Hub Indicator */}
      <circle r={boreRadius * 0.45} fill={isEngaged ? accentColor : "#cbd5e1"} />

      {/* Label */}
      {label && (
        <text
          y={outerRadius + 22}
          textAnchor="middle"
          fill={isEngaged ? accentColor : "#94a3b8"}
          fontSize="13"
          fontWeight={isEngaged ? "700" : "500"}
          letterSpacing="0.5px"
          style={{ textShadow: "0 2px 4px rgba(0,0,0,0.8)" }}
        >
          {label}
        </text>
      )}
    </g>
  );
};
