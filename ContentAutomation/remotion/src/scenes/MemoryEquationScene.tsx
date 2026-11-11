import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const MemoryEquationScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bar7B = spring({ frame: frame - 10, fps, config: { damping: 14 } });
  const bar70B = spring({ frame: frame - 25, fps, config: { damping: 14 } });
  const bar405B = spring({ frame: frame - 40, fps, config: { damping: 14 } });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#080914",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, Helvetica, sans-serif",
        color: "#ffffff",
        padding: "50px",
      }}
    >
      <div
        style={{
          color: "#38bdf8",
          fontSize: "20px",
          fontWeight: 700,
          letterSpacing: "2px",
          marginBottom: "10px",
        }}
      >
        THE MATHEMATICAL FORMULA
      </div>
      <h2 style={{ fontSize: "48px", fontWeight: 800, margin: "0 0 25px 0" }}>
        VRAM = Parameters × 2 Bytes (at FP16)
      </h2>

      {/* Comparison Bars */}
      <div
        style={{
          width: "100%",
          maxWidth: "1100px",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          marginTop: "20px",
        }}
      >
        {/* 7B Bar */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "20px" }}>
            <span style={{ fontWeight: 700 }}>7 Billion Parameters (e.g. Llama-3 8B, Mistral 7B)</span>
            <span style={{ color: "#38bdf8", fontWeight: 800 }}>14 GB VRAM</span>
          </div>
          <div style={{ width: "100%", height: "28px", backgroundColor: "#1e293b", borderRadius: "14px", overflow: "hidden" }}>
            <div
              style={{
                width: `${bar7B * 14}%`,
                height: "100%",
                background: "linear-gradient(90deg, #38bdf8, #818cf8)",
                borderRadius: "14px",
              }}
            />
          </div>
          <div style={{ fontSize: "15px", color: "#64748b", marginTop: "4px" }}>
            Fits comfortably on an RTX 3090, 4080, or 4090 GPU
          </div>
        </div>

        {/* 70B Bar */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "20px" }}>
            <span style={{ fontWeight: 700 }}>70 Billion Parameters (e.g. Llama-3 70B)</span>
            <span style={{ color: "#ec4899", fontWeight: 800 }}>140 GB VRAM</span>
          </div>
          <div style={{ width: "100%", height: "28px", backgroundColor: "#1e293b", borderRadius: "14px", overflow: "hidden" }}>
            <div
              style={{
                width: `${bar70B * 55}%`,
                height: "100%",
                background: "linear-gradient(90deg, #ec4899, #f43f5e)",
                borderRadius: "14px",
              }}
            />
          </div>
          <div style={{ fontSize: "15px", color: "#64748b", marginTop: "4px" }}>
            Requires 2× 80GB NVIDIA A100/H100 GPUs or Mac Studio 192GB
          </div>
        </div>

        {/* 405B Bar */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "20px" }}>
            <span style={{ fontWeight: 700 }}>405 Billion Parameters (Llama-3.1 405B)</span>
            <span style={{ color: "#f59e0b", fontWeight: 800 }}>810 GB VRAM</span>
          </div>
          <div style={{ width: "100%", height: "28px", backgroundColor: "#1e293b", borderRadius: "14px", overflow: "hidden" }}>
            <div
              style={{
                width: `${bar405B * 100}%`,
                height: "100%",
                background: "linear-gradient(90deg, #f59e0b, #ef4444)",
                borderRadius: "14px",
              }}
            />
          </div>
          <div style={{ fontSize: "15px", color: "#64748b", marginTop: "4px" }}>
            Requires a dedicated 8× H100 Enterprise Server Rack ($300,000+)
          </div>
        </div>
      </div>
    </div>
  );
};
