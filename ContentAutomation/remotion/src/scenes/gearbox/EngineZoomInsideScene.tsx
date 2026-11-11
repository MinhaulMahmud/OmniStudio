import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { EngineCrossSection } from "../../components/EngineCrossSection";

export const EngineZoomInsideScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Dynamic Camera Zoom penetrating inside the casing
  // Zoom scales from 1.0 -> 2.3, panning towards the lower-rear transmission compartment
  const zoomScale = interpolate(frame, [0, 80], [1.0, 2.2], {
    extrapolateRight: "clamp",
  });

  const panX = interpolate(frame, [0, 80], [0, -220], {
    extrapolateRight: "clamp",
  });

  const panY = interpolate(frame, [0, 80], [0, -180], {
    extrapolateRight: "clamp",
  });

  const scanLineY = (frame * 6) % 500;

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#060814",
        backgroundImage: "radial-gradient(circle at 60% 60%, #0d1e38 0%, #060814 70%)",
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
      {/* Header Info */}
      <div style={{ textAlign: "center", marginBottom: "20px", zIndex: 10 }}>
        <div
          style={{
            color: "#38bdf8",
            fontSize: "16px",
            fontWeight: 800,
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: "8px",
          }}
        >
          X-RAY PENETRATION // ENGINE CUTAWAY
        </div>
        <h2 style={{ fontSize: "48px", fontWeight: 900, margin: 0 }}>
          Where Is the Gearbox Situated?
        </h2>
        <p style={{ color: "#94a3b8", fontSize: "20px", margin: "8px 0 0 0" }}>
          Located directly behind and below the crankshaft in the shared wet crankcase
        </p>
      </div>

      {/* Main Viewport with Dynamic Zoom Camera */}
      <div
        style={{
          width: "1100px",
          height: "560px",
          backgroundColor: "#090d1a",
          borderRadius: "24px",
          border: "2px solid rgba(56, 189, 248, 0.4)",
          boxShadow: "0 0 60px rgba(56, 189, 248, 0.2)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Animated HUD Grid */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage:
              "linear-gradient(rgba(56, 189, 248, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.08) 1px, transparent 1px)",
            backgroundSize: "35px 35px",
            pointerEvents: "none",
          }}
        />

        {/* Laser Scan Line */}
        <div
          style={{
            position: "absolute",
            top: `${scanLineY}px`,
            left: 0,
            right: 0,
            height: "2px",
            backgroundColor: "#38bdf8",
            boxShadow: "0 0 12px #38bdf8, 0 0 24px #38bdf8",
            opacity: 0.6,
            pointerEvents: "none",
          }}
        />

        {/* Zooming Engine Transform Container */}
        <svg
          viewBox="0 0 600 450"
          style={{
            width: "100%",
            height: "100%",
            transform: `translate(${panX}px, ${panY}px) scale(${zoomScale})`,
            transformOrigin: "center center",
            transition: "transform 0.05s linear",
          }}
        >
          <EngineCrossSection
            scale={1.1}
            x={50}
            y={30}
            highlightTransmission={frame > 40}
          />
        </svg>

        {/* Overlay Callout Box appearing after zoom */}
        {frame > 50 && (
          <div
            style={{
              position: "absolute",
              right: "40px",
              bottom: "40px",
              width: "360px",
              backgroundColor: "rgba(15, 23, 42, 0.9)",
              border: "1px solid #38bdf8",
              borderRadius: "16px",
              padding: "20px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.8)",
              backdropFilter: "blur(10px)",
            }}
          >
            <div style={{ color: "#38bdf8", fontSize: "12px", fontWeight: 800, letterSpacing: "1px" }}>
              TRANSMISSION CAVITY
            </div>
            <div style={{ fontSize: "18px", fontWeight: 800, margin: "6px 0 10px 0" }}>
              Integrated Crankcase Compartment
            </div>
            <div style={{ fontSize: "14px", color: "#cbd5e1", lineHeight: "1.5" }}>
              Unlike cars which use separate gearboxes and dry bellhousings, 95% of motorcycles use a <strong>unit construction</strong> where the engine, wet multiplate clutch, and gearbox share the same oil bath.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
