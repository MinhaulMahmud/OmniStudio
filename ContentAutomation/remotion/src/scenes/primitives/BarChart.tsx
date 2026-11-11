import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface BarChartItem {
  label: string;
  value: number;
  formattedValue?: string;
  color?: string;
}

export interface BarChartProps {
  items: BarChartItem[];
  title?: string;
  maxValue?: number;
  width?: number | string;
  delayFrames?: number;
  layoutMode?: "landscape" | "portrait" | "square";
}

export const BarChart: React.FC<BarChartProps> = ({
  items,
  title,
  maxValue,
  width,
  delayFrames = 10,
  layoutMode = "landscape",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const effectiveWidth = width || (isPortrait ? "900px" : isSquare ? "860px" : "1000px");
  const computedMax = maxValue || Math.max(...items.map((i) => i.value), 1);

  return (
    <div
      style={{
        width: "100%",
        maxWidth: effectiveWidth,
        display: "flex",
        flexDirection: "column",
        gap: isPortrait ? "14px" : "18px",
        backgroundColor: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: isPortrait ? "20px 24px" : "28px 36px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.5)",
        boxSizing: "border-box",
      }}
    >
      {title && (
        <div style={{ fontSize: isPortrait ? "22px" : "20px", fontWeight: 800, color: "#f8fafc", marginBottom: "8px" }}>
          {title}
        </div>
      )}
      {items.map((item, idx) => {
        const itemDelay = delayFrames + idx * 8;
        const progress = interpolate(frame, [itemDelay, itemDelay + Math.round(fps * 0.8)], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const pct = Math.round((item.value / computedMax) * 100 * progress);
        const barColor = item.color || "#38bdf8";

        return (
          <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#e2e8f0", fontSize: isPortrait ? "18px" : "16px", fontWeight: 600 }}>
              <span>{item.label}</span>
              <span style={{ color: barColor, fontWeight: 700 }}>
                {item.formattedValue || `${item.value}`}
              </span>
            </div>
            <div
              style={{
                width: "100%",
                height: isPortrait ? "18px" : "16px",
                backgroundColor: "#1e293b",
                borderRadius: "8px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${pct}%`,
                  height: "100%",
                  backgroundColor: barColor,
                  borderRadius: "8px",
                  boxShadow: `0 0 12px ${barColor}66`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
