import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

export interface KineticTextProps {
  phrase: string;
  accentWords?: string[];
  fontSize?: number;
  color?: string;
  accentColor?: string;
  alignment?: "left" | "center" | "right";
  startFrame?: number;
}

export const KineticText: React.FC<KineticTextProps> = ({
  phrase,
  accentWords = [],
  fontSize = 64,
  color = "#ffffff",
  accentColor = "#00e5ff",
  alignment = "center",
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = phrase.trim().split(/\s+/);
  const normalizedAccents = accentWords.map((w) => w.toLowerCase().replace(/[^a-z0-9]/g, ""));

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: alignment === "left" ? "flex-start" : alignment === "right" ? "flex-end" : "center",
        alignItems: "center",
        gap: `${fontSize * 0.28}px`,
        maxWidth: "92%",
        margin: "0 auto",
      }}
    >
      {words.map((word, i) => {
        const cleanWord = word.toLowerCase().replace(/[^a-z0-9]/g, "");
        const isAccent = normalizedAccents.includes(cleanWord);

        const wordFrame = frame - startFrame - i * 3;
        const scale = spring({
          frame: wordFrame,
          fps,
          config: { damping: 12, stiffness: 220, mass: 0.8 },
        });

        const opacity = interpolate(wordFrame, [0, 4], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const translateY = interpolate(wordFrame, [0, 6], [18, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontSize: `${fontSize}px`,
              fontWeight: 800,
              fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              letterSpacing: "-0.03em",
              lineHeight: 1.15,
              color: isAccent ? accentColor : color,
              textShadow: isAccent
                ? `0 0 20px ${accentColor}88, 0 0 40px ${accentColor}44`
                : "0 2px 10px rgba(0,0,0,0.5)",
              transform: `scale(${Math.max(0, scale)}) translateY(${translateY}px)`,
              opacity,
              willChange: "transform, opacity",
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
