import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface TitleCardProps {
  title: string;
  subtitle?: string;
  badge?: string;
  accentColor?: string;
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
  badge = "TECHNICAL EXPLAINER",
  accentColor = "#38bdf8",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.6 },
  });

  const opacity = interpolate(frame, [0, Math.round(fps * 0.5)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "40px 60px",
        opacity,
      }}
    >
      {badge && (
        <div
          style={{
            padding: "6px 18px",
            borderRadius: "20px",
            backgroundColor: `${accentColor}22`,
            border: `1px solid ${accentColor}66`,
            color: accentColor,
            fontSize: "14px",
            fontWeight: 800,
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: "16px",
          }}
        >
          {badge}
        </div>
      )}
      <h1
        style={{
          fontSize: "56px",
          fontWeight: 900,
          margin: "0 0 16px 0",
          lineHeight: 1.15,
          maxWidth: "1400px",
          transform: `scale(${scale})`,
          background: "linear-gradient(135deg, #ffffff 40%, #c7d2fe 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          textShadow: `0 0 40px ${accentColor}44`,
        }}
      >
        {title}
      </h1>
      {subtitle && (
        <p
          style={{
            fontSize: "24px",
            color: "#94a3b8",
            maxWidth: "900px",
            margin: 0,
            lineHeight: 1.4,
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
};
