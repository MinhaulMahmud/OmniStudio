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
  layoutMode?: "landscape" | "portrait" | "square";
}

export const LineChart: React.FC<LineChartProps> = ({
  points,
  title,
  lineColor = "#38bdf8",
  fillColor = "rgba(56, 189, 248, 0.15)",
  width,
  height,
  delayFrames = 10,
  layoutMode = "landscape",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (points.length < 2) return null;

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const chartWidth = width || (isPortrait ? 850 : isSquare ? 800 : 900);
  const chartHeight = height || (isPortrait ? 380 : isSquare ? 340 : 360);

  const maxY = Math.max(...points.map((p) => p.y), 1);
  const minY = Math.min(...points.map((p) => p.y), 0);
  const rangeY = maxY - minY || 1;

  const chartPadding = { top: 30, right: 30, bottom: 40, left: 60 };
  const innerW = chartWidth - chartPadding.left - chartPadding.right;
  const innerH = chartHeight - chartPadding.top - chartPadding.bottom;

  const progress = interpolate(frame, [delayFrames, delayFrames + Math.round(fps * 1.0)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scaledPoints = points.map((p, idx) => {
    const px = chartPadding.left + (idx / (points.length - 1)) * innerW;
    const py = chartPadding.top + innerH - ((p.y - minY) / rangeY) * innerH;
    return { ...p, px, py };
  });

  const animatedLimit = Math.max(1, Math.floor(progress * (scaledPoints.length - 1)));
  const visiblePoints = scaledPoints.slice(0, animatedLimit + 1);

  const pathD = visiblePoints.reduce((acc, curr, idx) => {
    return idx === 0 ? `M ${curr.px} ${curr.py}` : `${acc} L ${curr.px} ${curr.py}`;
  }, "");

  const areaD =
    pathD &&
    `${pathD} L ${visiblePoints[visiblePoints.length - 1].px} ${chartPadding.top + innerH} L ${
      visiblePoints[0].px
    } ${chartPadding.top + innerH} Z`;

  return (
    <div
      style={{
        width: "100%",
        maxWidth: `${chartWidth}px`,
        backgroundColor: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: "24px 30px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.5)",
        boxSizing: "border-box",
      }}
    >
      {title && (
        <div style={{ fontSize: isPortrait ? "22px" : "20px", fontWeight: 800, color: "#f8fafc", marginBottom: "8px" }}>
          {title}
        </div>
      )}
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: "100%", height: "auto" }}>
        {/* Horizontal gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const y = chartPadding.top + innerH * (1 - pct);
          const val = Math.round(minY + rangeY * pct);
          return (
            <g key={i}>
              <line
                x1={chartPadding.left}
                y1={y}
                x2={chartPadding.left + innerW}
                y2={y}
                stroke="#334155"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
              <text x={chartPadding.left - 12} y={y + 4} fill="#64748b" fontSize="12" textAnchor="end">
                {val}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        {areaD && <path d={areaD} fill={fillColor} />}

        {/* Main trend line */}
        {pathD && <path d={pathD} fill="none" stroke={lineColor} strokeWidth="4" strokeLinecap="round" />}

        {/* Data points */}
        {visiblePoints.map((p, idx) => (
          <g key={idx}>
            <circle cx={p.px} cy={p.py} r="6" fill="#0f172a" stroke={lineColor} strokeWidth="3" />
            <text x={p.px} y={chartPadding.top + innerH + 24} fill="#94a3b8" fontSize="12" textAnchor="middle">
              {p.x}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};
