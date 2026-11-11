import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const WeightsMatrixScene: React.FC = () => {
  const frame = useCurrentFrame();

  const parameterCount = Math.floor(
    interpolate(frame, [0, 90], [1000000000, 70000000000], {
      extrapolateRight: "clamp",
    })
  );

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#050510",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, Helvetica, sans-serif",
        color: "#ffffff",
        position: "relative",
        padding: "40px",
      }}
    >
      <div
        style={{
          color: "#8b5cf6",
          fontSize: "20px",
          fontWeight: 700,
          letterSpacing: "2px",
          marginBottom: "10px",
        }}
      >
        UNDERSTANDING THE NUMBERS
      </div>
      <h2 style={{ fontSize: "52px", fontWeight: 800, margin: "0 0 30px 0" }}>
        What Exactly Are Model Weights?
      </h2>

      {/* Counter card */}
      <div
        style={{
          background: "linear-gradient(180deg, rgba(30, 27, 75, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)",
          border: "2px solid #6366f1",
          borderRadius: "24px",
          padding: "36px 60px",
          textAlign: "center",
          boxShadow: "0 0 50px rgba(99, 102, 241, 0.25)",
          marginBottom: "40px",
        }}
      >
        <div style={{ fontSize: "20px", color: "#a5b4fc", marginBottom: "8px" }}>
          ACTIVE PARAMETERS IN MEMORY
        </div>
        <div
          style={{
            fontSize: "72px",
            fontWeight: 900,
            fontFamily: "monospace",
            color: "#38bdf8",
            letterSpacing: "2px",
          }}
        >
          {parameterCount.toLocaleString()}
        </div>
        <div style={{ fontSize: "18px", color: "#94a3b8", marginTop: "10px" }}>
          Each parameter is a learned 16-bit floating point number (FP16)
        </div>
      </div>

      {/* Visual representation of weight matrix */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(8, 70px)",
          gap: "10px",
          opacity: 0.75,
        }}
      >
        {Array.from({ length: 24 }).map((_, i) => {
          const val = Math.sin(frame * 0.1 + i) * 0.8;
          return (
            <div
              key={i}
              style={{
                backgroundColor: val > 0 ? "rgba(99, 102, 241, 0.2)" : "rgba(236, 72, 153, 0.2)",
                border: `1px solid ${val > 0 ? "#6366f1" : "#ec4899"}`,
                borderRadius: "8px",
                height: "36px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "14px",
                fontFamily: "monospace",
                color: "#e2e8f0",
              }}
            >
              {val.toFixed(2)}
            </div>
          );
        })}
      </div>
    </div>
  );
};
