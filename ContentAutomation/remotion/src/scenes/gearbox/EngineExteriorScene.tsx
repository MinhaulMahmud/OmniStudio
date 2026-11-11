import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { EngineCrossSection } from "../../components/EngineCrossSection";

export const EngineExteriorScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.6 },
  });

  const subtitleOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#060913",
        backgroundImage: "radial-gradient(circle at 50% 20%, #0c1a30 0%, #060913 70%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, sans-serif",
        color: "#ffffff",
        position: "relative",
        overflow: "hidden",
        padding: "40px",
      }}
    >
      {/* Background blueprint grid */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage:
            "linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
          pointerEvents: "none",
        }}
      />

      {/* Category Pill */}
      <div
        style={{
          padding: "6px 18px",
          borderRadius: "20px",
          backgroundColor: "rgba(56, 189, 248, 0.15)",
          border: "1px solid rgba(56, 189, 248, 0.4)",
          color: "#38bdf8",
          fontSize: "14px",
          fontWeight: 700,
          letterSpacing: "2px",
          textTransform: "uppercase",
          marginBottom: "12px",
        }}
      >
        MECHANICAL ENGINEERING & AUTOMOTIVE
      </div>

      {/* Main Title */}
      <h1
        style={{
          transform: `scale(${titleScale})`,
          fontSize: "58px",
          fontWeight: 900,
          textAlign: "center",
          lineHeight: 1.15,
          margin: "0 0 16px 0",
          background: "linear-gradient(135deg, #ffffff 40%, #38bdf8 80%, #a855f7 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        HOW A MOTORCYCLE GEARBOX WORKS
      </h1>

      {/* Subtitle */}
      <p
        style={{
          opacity: subtitleOpacity,
          fontSize: "24px",
          color: "#94a3b8",
          maxWidth: "950px",
          textAlign: "center",
          margin: "0 0 35px 0",
        }}
      >
        Inside the Constant-Mesh Transmission: From Piston Combustion to Rear Wheel Drive
      </p>

      {/* Center Engine Animation Viewport */}
      <div
        style={{
          width: "900px",
          height: "460px",
          backgroundColor: "rgba(15, 23, 42, 0.8)",
          borderRadius: "24px",
          border: "1px solid rgba(56, 189, 248, 0.3)",
          boxShadow: "0 20px 50px rgba(0,0,0,0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <svg viewBox="0 0 520 400" style={{ width: "100%", height: "100%" }}>
          <EngineCrossSection scale={0.95} x={40} y={50} />
        </svg>

        {/* Engine Specs Overlay */}
        <div
          style={{
            position: "absolute",
            bottom: "16px",
            left: "24px",
            right: "24px",
            display: "flex",
            justifyContent: "space-between",
            backgroundColor: "rgba(7, 11, 20, 0.75)",
            backdropFilter: "blur(6px)",
            padding: "8px 20px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.08)",
            fontSize: "13px",
            color: "#cbd5e1",
          }}
        >
          <div>Cycle: <strong>4-Stroke DOHC</strong></div>
          <div>Crankshaft: <strong>Crossplane Counterweighted</strong></div>
          <div>Primary Drive: <strong>Helical Gear to Clutch</strong></div>
          <div>Transmission: <strong>6-Speed Constant Mesh</strong></div>
        </div>
      </div>
    </div>
  );
};
