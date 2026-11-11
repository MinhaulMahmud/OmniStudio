import React from "react";
import { useCurrentFrame } from "remotion";

export interface HUDTelemetryProps {
  label?: string;
  value?: string | number;
  size?: number;
  color?: string;
}

export const HUDTelemetry: React.FC<HUDTelemetryProps> = ({
  label = "TELEMETRY",
  value = "LIVE",
  size = 280,
  color = "#00e5ff",
}) => {
  const frame = useCurrentFrame();

  const rot1 = frame * 0.8;
  const rot2 = -frame * 0.5;

  return (
    <div
      style={{
        position: "relative",
        width: `${size}px`,
        height: `${size}px`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg
        width={size}
        height={size}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          transform: `rotate(${rot1}deg)`,
        }}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={size / 2 - 10}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeDasharray="18 12 6 12"
          opacity="0.4"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={size / 2 - 20}
          fill="none"
          stroke={color}
          strokeWidth="1"
          strokeDasharray="4 8"
          opacity="0.2"
        />
      </svg>

      <svg
        width={size * 0.75}
        height={size * 0.75}
        style={{
          position: "absolute",
          transform: `rotate(${rot2}deg)`,
        }}
      >
        <circle
          cx={(size * 0.75) / 2}
          cy={(size * 0.75) / 2}
          r={(size * 0.75) / 2 - 6}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeDasharray="45 80"
          opacity="0.7"
        />
      </svg>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 1,
          fontFamily: "'JetBrains Mono', monospace, sans-serif",
          letterSpacing: "0.15em",
        }}
      >
        <span
          style={{
            fontSize: `${Math.max(10, size * 0.05)}px`,
            color: "rgba(255,255,255,0.6)",
            textTransform: "uppercase",
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: `${Math.max(16, size * 0.12)}px`,
            fontWeight: 700,
            color,
            textShadow: `0 0 12px ${color}aa`,
            marginTop: "4px",
          }}
        >
          {value}
        </span>
      </div>
    </div>
  );
};
