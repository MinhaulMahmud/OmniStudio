import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const BandwidthScene: React.FC = () => {
  const frame = useCurrentFrame();

  const bandwidth = interpolate(frame, [0, 60], [200, 2000], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#060814",
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
          color: "#f43f5e",
          fontSize: "20px",
          fontWeight: 700,
          letterSpacing: "2px",
          marginBottom: "10px",
        }}
      >
        THE REAL BOTTLENECK
      </div>
      <h2 style={{ fontSize: "50px", fontWeight: 800, margin: "0 0 30px 0", textAlign: "center" }}>
        Text Generation Is Memory Bandwidth Bound
      </h2>

      {/* Visual Pipeline: VRAM -> Memory Bus -> Tensor Cores */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "20px",
          marginBottom: "40px",
        }}
      >
        {/* VRAM Pool */}
        <div
          style={{
            backgroundColor: "#1e1b4b",
            border: "2px solid #6366f1",
            borderRadius: "16px",
            padding: "24px",
            textAlign: "center",
            width: "220px",
          }}
        >
          <div style={{ fontSize: "36px" }}>💾</div>
          <div style={{ fontWeight: 800, fontSize: "20px", marginTop: "8px" }}>VRAM</div>
          <div style={{ color: "#94a3b8", fontSize: "14px" }}>Stores 140 GB Weights</div>
        </div>

        {/* Streaming Bus with animated pulse */}
        <div style={{ textAlign: "center", width: "260px" }}>
          <div style={{ color: "#f43f5e", fontWeight: 700, fontSize: "18px", marginBottom: "6px" }}>
            HIGH-SPEED BUS
          </div>
          <div
            style={{
              height: "8px",
              backgroundColor: "#334155",
              borderRadius: "4px",
              overflow: "hidden",
              position: "relative",
            }}
          >
            <div
              style={{
                position: "absolute",
                left: `${(frame * 5) % 100}%`,
                width: "60px",
                height: "100%",
                backgroundColor: "#f43f5e",
                borderRadius: "4px",
                boxShadow: "0 0 15px #f43f5e",
              }}
            />
          </div>
          <div style={{ color: "#a5b4fc", fontSize: "14px", marginTop: "8px" }}>
            {bandwidth.toFixed(0)} GB/s Throughput
          </div>
        </div>

        {/* Tensor Cores */}
        <div
          style={{
            backgroundColor: "#1e293b",
            border: "2px solid #38bdf8",
            borderRadius: "16px",
            padding: "24px",
            textAlign: "center",
            width: "220px",
          }}
        >
          <div style={{ fontSize: "36px" }}>⚡</div>
          <div style={{ fontWeight: 800, fontSize: "20px", marginTop: "8px" }}>TENSOR CORES</div>
          <div style={{ color: "#94a3b8", fontSize: "14px" }}>Generates 1 Token</div>
        </div>
      </div>

      <div
        style={{
          backgroundColor: "rgba(244, 63, 94, 0.1)",
          border: "1px solid rgba(244, 63, 94, 0.3)",
          borderRadius: "12px",
          padding: "16px 28px",
          maxWidth: "800px",
          textAlign: "center",
          fontSize: "18px",
          color: "#fecdd3",
        }}
      >
        💡 <strong>Key Rule:</strong> To output just <strong>ONE single word</strong>, the GPU must transfer 
        all active weights from VRAM across the bus into compute registers!
      </div>
    </div>
  );
};
