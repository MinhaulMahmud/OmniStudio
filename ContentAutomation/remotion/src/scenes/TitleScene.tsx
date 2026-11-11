import React from "react";
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.5 },
  });

  const subtitleOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const badgeY = interpolate(frame, [25, 45], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const cardOffset = interpolate(frame, [35, 60], [100, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#080816",
        backgroundImage:
          "radial-gradient(circle at 50% 20%, #1e1145 0%, #080816 70%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, Helvetica, sans-serif",
        color: "#ffffff",
        padding: "40px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative background grid */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          opacity: 0.8,
        }}
      />

      {/* Voice Studio badge */}
      <div
        style={{
          transform: `translateY(${badgeY}px)`,
          opacity: subtitleOpacity,
          backgroundColor: "rgba(139, 92, 246, 0.15)",
          border: "1px solid rgba(139, 92, 246, 0.5)",
          borderRadius: "50px",
          padding: "10px 24px",
          fontSize: "20px",
          fontWeight: 600,
          color: "#a78bfa",
          letterSpacing: "1.5px",
          marginBottom: "30px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <span>🎙️</span> NARRATED BY MINHAZ (VOICESTUDIO CLONED VOICE)
      </div>

      {/* Main Title */}
      <h1
        style={{
          transform: `scale(${titleScale})`,
          fontSize: "64px",
          fontWeight: 900,
          textAlign: "center",
          lineHeight: 1.15,
          maxWidth: "1300px",
          margin: "0 0 20px 0",
          background: "linear-gradient(135deg, #ffffff 30%, #8b5cf6 80%, #38bdf8 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          textShadow: "0 0 40px rgba(139, 92, 246, 0.3)",
        }}
      >
        HOW AI MODEL WEIGHTS DETERMINE COMPUTE POWER
      </h1>

      {/* Subtitle */}
      <p
        style={{
          opacity: subtitleOpacity,
          fontSize: "28px",
          fontWeight: 400,
          color: "#94a3b8",
          maxWidth: "850px",
          textAlign: "center",
          margin: "0 0 50px 0",
        }}
      >
        Why larger LLMs demand exponential VRAM and memory bandwidth
      </p>

      {/* Model Cards Comparison: 7B vs 70B */}
      <div
        style={{
          display: "flex",
          gap: "40px",
          transform: `translateY(${cardOffset}px)`,
          opacity: subtitleOpacity,
        }}
      >
        {/* 7B Card */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            borderRadius: "20px",
            padding: "24px 36px",
            textAlign: "center",
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
          }}
        >
          <div style={{ color: "#38bdf8", fontSize: "18px", fontWeight: 700 }}>
            SMALL MODEL
          </div>
          <div style={{ fontSize: "44px", fontWeight: 800, margin: "6px 0" }}>
            7 Billion
          </div>
          <div style={{ color: "#64748b", fontSize: "16px" }}>
            ~14 GB VRAM • Runs on Laptop
          </div>
        </div>

        {/* VS circle */}
        <div
          style={{
            alignSelf: "center",
            width: "50px",
            height: "50px",
            borderRadius: "25px",
            backgroundColor: "#1e1b4b",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 800,
            color: "#818cf8",
          }}
        >
          VS
        </div>

        {/* 70B Card */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(236, 72, 153, 0.4)",
            borderRadius: "20px",
            padding: "24px 36px",
            textAlign: "center",
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
          }}
        >
          <div style={{ color: "#ec4899", fontSize: "18px", fontWeight: 700 }}>
            LARGE MODEL
          </div>
          <div style={{ fontSize: "44px", fontWeight: 800, margin: "6px 0" }}>
            70 Billion
          </div>
          <div style={{ color: "#64748b", fontSize: "16px" }}>
            ~140 GB VRAM • Demands Server GPU Cluster
          </div>
        </div>
      </div>
    </div>
  );
};
