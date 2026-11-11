import React from "react";
import { useCurrentFrame } from "remotion";

export interface DynamicBackdropProps {
  theme?: "cyber" | "aurora" | "dark-slate" | "space";
  particleCount?: number;
  showGrid?: boolean;
}

export const DynamicBackdrop: React.FC<DynamicBackdropProps> = ({
  theme = "aurora",
  particleCount = 24,
  showGrid = true,
}) => {
  const frame = useCurrentFrame();

  const angle1 = frame * 0.02;
  const angle2 = frame * 0.015;

  const x1 = 50 + Math.sin(angle1) * 20;
  const y1 = 40 + Math.cos(angle1) * 15;
  const x2 = 60 + Math.cos(angle2) * 25;
  const y2 = 70 + Math.sin(angle2) * 20;

  const themeColors = {
    aurora: {
      bg: "#050711",
      glow1: "rgba(0, 210, 255, 0.16)",
      glow2: "rgba(120, 0, 255, 0.14)",
      grid: "rgba(255, 255, 255, 0.03)",
      particle: "rgba(0, 220, 255, 0.5)",
    },
    cyber: {
      bg: "#08090f",
      glow1: "rgba(255, 0, 110, 0.15)",
      glow2: "rgba(0, 245, 212, 0.15)",
      grid: "rgba(0, 245, 212, 0.04)",
      particle: "rgba(255, 200, 0, 0.6)",
    },
    "dark-slate": {
      bg: "#090d16",
      glow1: "rgba(56, 189, 248, 0.12)",
      glow2: "rgba(99, 102, 241, 0.12)",
      grid: "rgba(255, 255, 255, 0.02)",
      particle: "rgba(255, 255, 255, 0.4)",
    },
    space: {
      bg: "#030408",
      glow1: "rgba(147, 51, 234, 0.18)",
      glow2: "rgba(59, 130, 246, 0.15)",
      grid: "rgba(147, 51, 234, 0.03)",
      particle: "rgba(255, 255, 255, 0.7)",
    },
  }[theme];

  const particles = Array.from({ length: particleCount }).map((_, i) => {
    const seedX = (i * 137.5) % 100;
    const speed = 0.3 + (i % 5) * 0.15;
    const currentY = (100 - ((frame * speed + i * 20) % 110));
    const opacity = 0.2 + 0.4 * Math.sin(frame * 0.05 + i);
    const size = 2 + (i % 3) * 1.5;

    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: `${seedX}%`,
          top: `${currentY}%`,
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: "50%",
          backgroundColor: themeColors.particle,
          opacity,
          boxShadow: `0 0 8px ${themeColors.particle}`,
          pointerEvents: "none",
        }}
      />
    );
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        backgroundColor: themeColors.bg,
        overflow: "hidden",
        zIndex: 0,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: `${y1 - 30}%`,
          left: `${x1 - 30}%`,
          width: "60vw",
          height: "60vw",
          borderRadius: "50%",
          background: `radial-gradient(circle, ${themeColors.glow1} 0%, transparent 70%)`,
          filter: "blur(60px)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: `${y2 - 30}%`,
          left: `${x2 - 30}%`,
          width: "70vw",
          height: "70vw",
          borderRadius: "50%",
          background: `radial-gradient(circle, ${themeColors.glow2} 0%, transparent 70%)`,
          filter: "blur(70px)",
          pointerEvents: "none",
        }}
      />

      {showGrid && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            backgroundImage: `linear-gradient(${themeColors.grid} 1px, transparent 1px), linear-gradient(90deg, ${themeColors.grid} 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
            maskImage: "radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, transparent 75%)",
            WebkitMaskImage: "radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, transparent 75%)",
            pointerEvents: "none",
          }}
        />
      )}

      {particles}

      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background: "radial-gradient(circle at center, transparent 40%, rgba(0,0,0,0.6) 100%)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
};
