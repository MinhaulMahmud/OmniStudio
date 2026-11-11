import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface LineChartPoint {
  x: string | number;
  y: number;
}

export interface LineChartProps {
  points: LineChartPoint[];
  title?: string;
  lineColor?: string;
  fillColor?: string;
  width?: number;
  height?: number;
  delayFrames?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  points,
  title,
  lineColor = "#38bdf8",
  fillColor = "rgba(56, 189, 248, 0.15)",
  width = 900,
  height = 360,
  delayFrames = 10,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (points.length < 2) return null;

  const maxY = Math.max(...points.map((p) => p.y), 1);
  const minY = Math.min(...points.map((p) => p.y), 0);
  const rangeY = maxY - minY || 1;

  const chartPadding = { top: 30, right: 30, bottom: 40, left: 60 };
  const innerW = width - chartPadding.left - chartPadding.right;
  const innerH = height - chartPadding.top - chartPadding.bottom;

  // Animation progress (0 to 1)
  const progress = interpolate(frame, [delayFrames, delayFrames + Math.round(fps * 1.0)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scaledPoints = points.map((p, idx) => {
    const px = chartPadding.left + (idx / (points.length - 1)) * innerW;
    const py = chartPadding.top + innerH - ((p.y - minY) / rangeY) * innerH;
    return { ...p, px, py };
  });

  // Calculate visible path length
  const pathD = scaledPoints
    .map((p, idx) => (idx === 0 ? `M ${p.px} ${p.py}` : `L ${p.px} ${p.py}`))
    .join(" ");

  const areaD = `${pathD} L ${chartPadding.left + innerW} ${chartPadding.top + innerH} L ${chartPadding.left} ${chartPadding.top + innerH} Z`;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: "rgba(15, 23, 42, 0.85)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: "20px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.5)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {title && (
        <div style={{ fontSize: "18px", fontWeight: 800, color: "#f8fafc", marginBottom: "8px" }}>
          {title}
        </div>
      )}
      <svg viewBox={`0 0 ${width} ${height - 40}`} style={{ width: "100%", height: "100%" }}>
        {/* Horizontal gridlines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((frac, i) => {
          const gy = chartPadding.top + innerH * (1 - frac);
          return (
            <line
              key={i}
              x1={chartPadding.left}
              y1={gy}
              x2={chartPadding.left + innerW}
              y2={gy}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Shaded Area */}
        <path d={areaD} fill={fillColor} opacity={progress} />

        {/* Animated Line */}
        <path
          d={pathD}
          fill="none"
          stroke={lineColor}
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="2000"
          strokeDashoffset={2000 * (1 - progress)}
          style={{ filter: `drop-shadow(0 0 8px ${lineColor})` }}
        />

        {/* Data points */}
        {scaledPoints.map((p, idx) => {
          const pointStart = delayFrames + Math.round((idx / points.length) * fps * 0.8);
          const pScale = interpolate(frame, [pointStart, pointStart + 10], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <g key={idx} transform={`translate(${p.px}, ${p.py}) scale(${pScale})`}>
              <circle r="5" fill="#0f172a" stroke={lineColor} strokeWidth="2.5" />
            </g>
          );
        })}
      </svg>
    </div>
  );
};
