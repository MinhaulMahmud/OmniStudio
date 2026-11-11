import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const QuantizationScene: React.FC = () => {
  const frame = useCurrentFrame();

  const compressionRatio = interpolate(frame, [15, 45], [1, 4], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#070815",
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
          color: "#10b981",
          fontSize: "20px",
          fontWeight: 700,
          letterSpacing: "2px",
          marginBottom: "10px",
        }}
      >
        THE EFFICIENCY SOLUTION
      </div>
      <h2 style={{ fontSize: "50px", fontWeight: 800, margin: "0 0 35px 0" }}>
        Quantization: 4× Compute & Memory Compression
      </h2>

      {/* Side-by-side comparison */}
      <div
        style={{
          display: "flex",
          gap: "50px",
          alignItems: "center",
          marginBottom: "30px",
        }}
      >
        {/* FP16 Box */}
        <div
          style={{
            backgroundColor: "#1e1b4b",
            border: "2px solid #818cf8",
            borderRadius: "20px",
            padding: "30px 40px",
            textAlign: "center",
            width: "300px",
          }}
        >
          <div style={{ fontSize: "22px", color: "#a5b4fc", fontWeight: 700 }}>
            STANDARD FP16
          </div>
          <div style={{ fontSize: "40px", fontWeight: 800, margin: "10px 0" }}>
            16 Bits
          </div>
          <div style={{ color: "#cbd5e1", fontSize: "16px" }}>2 Bytes per parameter</div>
          <div style={{ marginTop: "15px", color: "#f43f5e", fontWeight: 700 }}>
            70B Model = 140 GB VRAM
          </div>
        </div>

        {/* Compression arrow */}
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "36px", color: "#10b981" }}>➔</div>
          <div style={{ color: "#34d399", fontWeight: 800, fontSize: "20px" }}>
            {compressionRatio.toFixed(1)}× SMALLER
          </div>
        </div>

        {/* INT4 Box */}
        <div
          style={{
            backgroundColor: "#064e3b",
            border: "2px solid #34d399",
            borderRadius: "20px",
            padding: "30px 40px",
            textAlign: "center",
            width: "300px",
            boxShadow: "0 0 40px rgba(52, 211, 153, 0.2)",
          }}
        >
          <div style={{ fontSize: "22px", color: "#6ee7b7", fontWeight: 700 }}>
            QUANTIZED INT4
          </div>
          <div style={{ fontSize: "40px", fontWeight: 800, margin: "10px 0" }}>
            4 Bits
          </div>
          <div style={{ color: "#cbd5e1", fontSize: "16px" }}>0.5 Bytes per parameter</div>
          <div style={{ marginTop: "15px", color: "#34d399", fontWeight: 800 }}>
            70B Model = 35 GB VRAM!
          </div>
        </div>
      </div>

      <p style={{ color: "#94a3b8", fontSize: "20px", maxWidth: "800px", textAlign: "center" }}>
        Quantization allows models like <strong>Llama-3 70B</strong> to run locally on dual RTX 3090/4090 GPUs 
        or an Apple Mac Studio, with negligible accuracy loss.
      </p>
    </div>
  );
};
