import React from "react";
import { useCurrentFrame } from "remotion";
import { SequentialGearboxMechanism } from "../../components/SequentialGearboxMechanism";

export const ConstantMeshMechanismScene: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#050813",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Roboto, sans-serif",
        color: "#ffffff",
        position: "relative",
        padding: "30px 40px",
      }}
    >
      {/* Title Header */}
      <div style={{ textAlign: "center", marginBottom: "16px" }}>
        <div
          style={{
            color: "#f59e0b",
            fontSize: "15px",
            fontWeight: 800,
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: "6px",
          }}
        >
          CORE MECHANISM // CONSTANT MESH & DOG CLUTCHES
        </div>
        <h2 style={{ fontSize: "44px", fontWeight: 900, margin: 0 }}>
          How All 6 Gears Spin Together in Constant Mesh
        </h2>
        <p style={{ color: "#94a3b8", fontSize: "19px", margin: "6px 0 0 0" }}>
          Every gear pair is permanently meshed. Shifting works by sliding <strong>dog rings</strong> into gear pockets!
        </p>
      </div>

      {/* Main 6-Speed Transmission Animated Mechanical Simulator */}
      <SequentialGearboxMechanism
        width={1300}
        height={580}
        inputRpm={6500}
        showTorquePath={true}
      />
    </div>
  );
};
