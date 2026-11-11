import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const ShiftingAndRatiosScene: React.FC = () => {
  const frame = useCurrentFrame();

  const ratios = [
    { gear: "1st Gear", ratio: 2.85, teeth: "13T / 37T", torque: "+185%", maxSpeed: "52 km/h", use: "Launch from dead stop" },
    { gear: "2nd Gear", ratio: 1.88, teeth: "17T / 32T", torque: "+88%", maxSpeed: "79 km/h", use: "City acceleration & turns" },
    { gear: "3rd Gear", ratio: 1.40, teeth: "20T / 28T", torque: "+40%", maxSpeed: "106 km/h", use: "Overtaking & urban speeds" },
    { gear: "4th Gear", ratio: 1.14, teeth: "22T / 25T", torque: "+14%", maxSpeed: "130 km/h", use: "Cruising speed transition" },
    { gear: "5th Gear", ratio: 0.96, teeth: "24T / 23T", torque: "Direct", maxSpeed: "155 km/h", use: "Highway cruising" },
    { gear: "6th Gear", ratio: 0.81, teeth: "26T / 21T", torque: "-19% (OD)", maxSpeed: "185 km/h", use: "High-speed fuel efficiency" },
  ];

  const activeIdx = Math.min(5, Math.floor((frame / 40) % 6));

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#060913",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, sans-serif",
        color: "#ffffff",
        position: "relative",
        padding: "40px",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: "30px" }}>
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
          TORQUE MULTIPLICATION VS TOP SPEED
        </div>
        <h2 style={{ fontSize: "48px", fontWeight: 900, margin: 0 }}>
          Why Bikes Need Different Gear Ratios
        </h2>
        <p style={{ color: "#94a3b8", fontSize: "20px", margin: "8px 0 0 0" }}>
          Internal combustion engines produce narrow peak torque. Gears trade RPM for wheel torque.
        </p>
      </div>

      {/* Grid of 6 Gear Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 380px)",
          gap: "24px",
          maxWidth: "1200px",
        }}
      >
        {ratios.map((r, i) => {
          const isSelected = i === activeIdx;
          return (
            <div
              key={r.gear}
              style={{
                backgroundColor: isSelected ? "rgba(2, 132, 199, 0.2)" : "rgba(15, 23, 42, 0.75)",
                border: isSelected ? "2px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "20px",
                padding: "24px 28px",
                boxShadow: isSelected ? "0 0 35px rgba(56, 189, 248, 0.35)" : "0 10px 25px rgba(0,0,0,0.5)",
                transform: isSelected ? "scale(1.03)" : "scale(1.0)",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <span style={{ fontSize: "22px", fontWeight: 800, color: isSelected ? "#38bdf8" : "#ffffff" }}>
                  {r.gear}
                </span>
                <span
                  style={{
                    backgroundColor: isSelected ? "#38bdf8" : "rgba(255,255,255,0.1)",
                    color: isSelected ? "#000000" : "#cbd5e1",
                    fontSize: "14px",
                    fontWeight: 800,
                    padding: "3px 10px",
                    borderRadius: "8px",
                  }}
                >
                  {r.ratio}:1
                </span>
              </div>

              <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "6px" }}>
                Teeth: <strong style={{ color: "#e2e8f0" }}>{r.teeth}</strong>
              </div>
              <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "6px" }}>
                Torque Gain: <strong style={{ color: i <= 2 ? "#22c55e" : "#f59e0b" }}>{r.torque}</strong>
              </div>
              <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "12px" }}>
                Top Speed: <strong style={{ color: "#38bdf8" }}>{r.maxSpeed}</strong>
              </div>

              <div
                style={{
                  fontSize: "13px",
                  color: isSelected ? "#e0f2fe" : "#64748b",
                  borderTop: "1px solid rgba(255,255,255,0.08)",
                  paddingTop: "10px",
                }}
              >
                {r.use}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
