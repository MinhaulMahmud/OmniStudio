import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, config: { damping: 12 } });
  const opacity = interpolate(frame, [10, 30], [0, 1]);

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#070817",
        backgroundImage:
          "radial-gradient(circle at 50% 50%, #1e1145 0%, #070817 80%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, Helvetica, sans-serif",
        color: "#ffffff",
        padding: "40px",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
          maxWidth: "900px",
        }}
      >
        <div
          style={{
            fontSize: "24px",
            color: "#a78bfa",
            fontWeight: 700,
            letterSpacing: "3px",
            marginBottom: "15px",
          }}
        >
          SUMMARY & TAKEAWAY
        </div>
        <h2 style={{ fontSize: "52px", fontWeight: 900, marginBottom: "30px", lineHeight: 1.2 }}>
          Model Weights = The True Measure of AI Compute
        </h2>

        {/* 3 bullet summary */}
        <div
          style={{
            opacity,
            backgroundColor: "rgba(15, 23, 42, 0.7)",
            border: "1px solid rgba(139, 92, 246, 0.3)",
            borderRadius: "20px",
            padding: "30px 40px",
            textAlign: "left",
            display: "flex",
            flexDirection: "column",
            gap: "18px",
            fontSize: "20px",
            marginBottom: "35px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ color: "#38bdf8" }}>✓</span>
            <span><strong>Parameters</strong> determine baseline memory requirements (2 bytes each).</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ color: "#ec4899" }}>✓</span>
            <span><strong>Memory Bandwidth</strong> dictates tokens generated per second.</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ color: "#34d399" }}>✓</span>
            <span><strong>Quantization (4-bit/8-bit)</strong> is essential for accessible local AI inference.</span>
          </div>
        </div>

        {/* CTA */}
        <div style={{ opacity, fontSize: "22px", color: "#f1f5f9" }}>
          🚀 <strong>Follow for more AI Engineering Deep Dives!</strong>
        </div>
        <div style={{ opacity, fontSize: "16px", color: "#64748b", marginTop: "10px" }}>
          Audio Voiced by Minhaz (VoiceStudio) • Visuals Rendered by Remotion
        </div>
      </div>
    </div>
  );
};
