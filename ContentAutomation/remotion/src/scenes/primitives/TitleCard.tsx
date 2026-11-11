import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface TitleCardProps {
  title: string;
  subtitle?: string;
  badge?: string;
  accentColor?: string;
  layoutMode?: "landscape" | "portrait" | "square";
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
  badge = "TECHNICAL EXPLAINER",
  accentColor = "#38bdf8",
  layoutMode = "landscape",
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

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const titleFontSize = isPortrait
    ? (title.length > 50 ? "42px" : title.length > 30 ? "52px" : "62px")
    : isSquare
    ? (title.length > 50 ? "40px" : "48px")
    : (title.length > 50 ? "58px" : "72px");

  const subtitleFontSize = isPortrait ? "28px" : isSquare ? "26px" : "32px";
  const maxWidth = isPortrait ? "900px" : isSquare ? "860px" : "1500px";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        maxWidth,
        width: "100%",
        padding: isPortrait ? "10px 20px" : "20px 40px",
        opacity,
        boxSizing: "border-box",
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
            fontSize: isPortrait ? "18px" : "20px",
            fontWeight: 700,
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: isPortrait ? "16px" : "24px",
            display: "inline-block",
          }}
        >
          {badge}
        </div>
      )}
      <h1
        style={{
          fontSize: titleFontSize,
          fontWeight: 900,
          color: "#f8fafc",
          margin: 0,
          lineHeight: 1.15,
          letterSpacing: "-1px",
          transform: `scale(${scale})`,
          textShadow: "0 4px 24px rgba(0,0,0,0.7)",
          overflowWrap: "break-word",
          wordBreak: "break-word",
        }}
      >
        {title}
      </h1>
      {subtitle && (
        <p
          style={{
            fontSize: subtitleFontSize,
            fontWeight: 400,
            color: "#94a3b8",
            marginTop: isPortrait ? "12px" : "18px",
            marginBottom: 0,
            maxWidth: isPortrait ? "840px" : "1100px",
            lineHeight: 1.4,
            overflowWrap: "break-word",
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
};
