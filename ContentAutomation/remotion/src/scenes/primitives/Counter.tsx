import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface CounterProps {
  toValue: number;
  label: string;
  fromValue?: number;
  unit?: string;
  prefix?: string;
  accentColor?: string;
  durationFrames?: number;
  subtext?: string;
}

export const Counter: React.FC<CounterProps> = ({
  toValue,
  label,
  fromValue = 0,
  unit = "",
  prefix = "",
  accentColor = "#38bdf8",
  durationFrames,
  subtext,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const totalDuration = durationFrames || Math.round(fps * 2.0);

  const currentValue = Math.floor(
    interpolate(frame, [0, totalDuration], [fromValue, toValue], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(15, 23, 42, 0.85)",
        border: `1.5px solid ${accentColor}66`,
        borderRadius: "24px",
        padding: "32px 50px",
        boxShadow: `0 10px 30px rgba(0,0,0,0.5), 0 0 30px ${accentColor}22`,
        textAlign: "center",
      }}
    >
      <div
        style={{
          fontSize: "14px",
          fontWeight: 800,
          color: accentColor,
          letterSpacing: "2px",
          textTransform: "uppercase",
          marginBottom: "10px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: "64px",
          fontWeight: 900,
          fontFamily: "monospace",
          color: "#ffffff",
          letterSpacing: "1px",
        }}
      >
        {prefix}
        {currentValue.toLocaleString()}
        {unit && <span style={{ fontSize: "36px", color: accentColor, marginLeft: "6px" }}>{unit}</span>}
      </div>
      {subtext && (
        <div style={{ fontSize: "16px", color: "#94a3b8", marginTop: "8px" }}>
          {subtext}
        </div>
      )}
    </div>
  );
};
