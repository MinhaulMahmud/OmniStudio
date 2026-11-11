import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface BulletRevealProps {
  bullets: string[];
  accentColor?: string;
  delayFrames?: number;
  staggerFrames?: number;
  maxWidth?: string | number;
  layoutMode?: "landscape" | "portrait" | "square";
}

export const BulletReveal: React.FC<BulletRevealProps> = ({
  bullets,
  accentColor = "#38bdf8",
  delayFrames = 10,
  staggerFrames = 20,
  maxWidth,
  layoutMode = "landscape",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const effectiveMaxWidth = maxWidth || (isPortrait ? "900px" : isSquare ? "860px" : "1200px");
  const fontSize = isPortrait ? "26px" : isSquare ? "24px" : "28px";
  const badgeSize = isPortrait ? "32px" : isSquare ? "30px" : "36px";
  const padding = isPortrait ? "14px 20px" : "18px 24px";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: isPortrait ? "12px" : "16px",
        width: "100%",
        maxWidth: effectiveMaxWidth,
        boxSizing: "border-box",
      }}
    >
      {bullets.map((bullet, idx) => {
        const start = delayFrames + idx * staggerFrames;
        const opacity = interpolate(frame, [start, start + Math.round(fps * 0.4)], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const translateY = interpolate(frame, [start, start + Math.round(fps * 0.4)], [20, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={idx}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: isPortrait ? "14px" : "18px",
              padding,
              borderRadius: "16px",
              backgroundColor: "rgba(15, 23, 42, 0.75)",
              border: "1px solid rgba(148, 163, 184, 0.15)",
              boxShadow: "0 8px 30px rgba(0,0,0,0.35)",
              opacity,
              transform: `translateY(${translateY}px)`,
            }}
          >
            <div
              style={{
                width: badgeSize,
                height: badgeSize,
                borderRadius: "50%",
                backgroundColor: `${accentColor}22`,
                border: `1.5px solid ${accentColor}`,
                color: accentColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: isPortrait ? "16px" : "18px",
                fontWeight: 800,
                flexShrink: 0,
              }}
            >
              {idx + 1}
            </div>
            <div
              style={{
                color: "#e2e8f0",
                fontSize,
                fontWeight: 500,
                lineHeight: 1.4,
                overflowWrap: "break-word",
              }}
            >
              {bullet}
            </div>
          </div>
        );
      })}
    </div>
  );
};
