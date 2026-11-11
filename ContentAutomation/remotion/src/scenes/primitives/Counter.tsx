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
  layoutMode?: "landscape" | "portrait" | "square";
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
  layoutMode = "landscape",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const totalDuration = durationFrames || Math.round(fps * 2.0);

  const currentValue = Math.floor(
    interpolate(frame, [0, totalDuration], [fromValue, toValue], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );

  const numberFontSize = isPortrait ? "56px" : isSquare ? "50px" : "64px";
  const labelFontSize = isPortrait ? "20px" : isSquare ? "18px" : "20px";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: isPortrait ? "24px 32px" : "28px 40px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.5)",
        minWidth: isPortrait ? "220px" : "240px",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          fontSize: numberFontSize,
          fontWeight: 900,
          color: accentColor,
          lineHeight: 1,
          fontFamily: "monospace",
          textShadow: `0 0 30px ${accentColor}44`,
        }}
      >
        {prefix}
        {currentValue.toLocaleString()}
        {unit}
      </div>
      <div
        style={{
          fontSize: labelFontSize,
          fontWeight: 700,
          color: "#f8fafc",
          marginTop: "12px",
          textAlign: "center",
        }}
      >
        {label}
      </div>
      {subtext && (
        <div
          style={{
            fontSize: "14px",
            color: "#94a3b8",
            marginTop: "6px",
            textAlign: "center",
          }}
        >
          {subtext}
        </div>
      )}
    </div>
  );
};
