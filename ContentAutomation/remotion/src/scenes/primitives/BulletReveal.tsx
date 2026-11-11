import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface BulletRevealProps {
  bullets: string[];
  accentColor?: string;
  delayFrames?: number;
  staggerFrames?: number;
  maxWidth?: string | number;
}

export const BulletReveal: React.FC<BulletRevealProps> = ({
  bullets,
  accentColor = "#38bdf8",
  delayFrames = 10,
  staggerFrames = 20,
  maxWidth = 1000,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        width: "100%",
        maxWidth,
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
              gap: "18px",
              padding: "18px 24px",
              backgroundColor: "rgba(15, 23, 42, 0.75)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "16px",
              boxShadow: "0 10px 25px rgba(0, 0, 0, 0.4)",
              opacity,
              transform: `translateY(${translateY}px)`,
            }}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "10px",
                backgroundColor: `${accentColor}22`,
                border: `1.5px solid ${accentColor}`,
                color: accentColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 800,
                fontSize: "15px",
                flexShrink: 0,
              }}
            >
              {idx + 1}
            </div>
            <p
              style={{
                margin: 0,
                fontSize: "20px",
                lineHeight: 1.45,
                color: "#e2e8f0",
                fontWeight: 500,
              }}
            >
              {bullet}
            </p>
          </div>
        );
      })}
    </div>
  );
};
