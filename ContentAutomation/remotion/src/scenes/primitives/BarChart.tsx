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
}

export const BarChart: React.FC<BarChartProps> = ({
  items,
  title,
  maxValue,
  width = 900,
  delayFrames = 10,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const computedMax = maxValue || Math.max(...items.map((i) => i.value), 1);

  return (
    <div
      style={{
        width,
        display: "flex",
        flexDirection: "column",
        gap: "18px",
        backgroundColor: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: "28px 36px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.5)",
      }}
    >
      {title && (
        <div style={{ fontSize: "20px", fontWeight: 800, color: "#f8fafc", marginBottom: "8px" }}>
          {title}
        </div>
      )}
      {items.map((item, idx) => {
        const start = delayFrames + idx * Math.round(fps * 0.3);
        const progress = interpolate(frame, [start, start + Math.round(fps * 0.6)], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const targetPercent = (item.value / computedMax) * 100;
        const currentPercent = targetPercent * progress;
        const barColor = item.color || (idx % 2 === 0 ? "#38bdf8" : "#818cf8");

        return (
          <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "16px", color: "#cbd5e1" }}>
              <span style={{ fontWeight: 600 }}>{item.label}</span>
              <span style={{ fontWeight: 700, color: barColor }}>
                {item.formattedValue || item.value.toLocaleString()}
              </span>
            </div>
            <div
              style={{
                height: "16px",
                backgroundColor: "rgba(255, 255, 255, 0.08)",
                borderRadius: "8px",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${currentPercent}%`,
                  backgroundColor: barColor,
                  borderRadius: "8px",
                  boxShadow: `0 0 12px ${barColor}88`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
