import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

export interface EnergyPulseProps {
  color?: string;
  size?: number;
  period?: number;
}

export const EnergyPulse: React.FC<EnergyPulseProps> = ({
  color = "#00e5ff",
  size = 300,
  period = 45,
}) => {
  const frame = useCurrentFrame();

  const cycle1 = (frame % period) / period;
  const cycle2 = ((frame + period / 2) % period) / period;

  const scale1 = interpolate(cycle1, [0, 1], [0.3, 1.4]);
  const opacity1 = interpolate(cycle1, [0, 0.4, 1], [0.7, 0.4, 0]);

  const scale2 = interpolate(cycle2, [0, 1], [0.3, 1.4]);
  const opacity2 = interpolate(cycle2, [0, 0.4, 1], [0.7, 0.4, 0]);

  return (
    <div
      style={{
        position: "relative",
        width: `${size}px`,
        height: `${size}px`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: "50%",
          border: `2px solid ${color}`,
          transform: `scale(${scale1})`,
          opacity: opacity1,
          boxShadow: `0 0 20px ${color}88`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: "50%",
          border: `2px solid ${color}`,
          transform: `scale(${scale2})`,
          opacity: opacity2,
          boxShadow: `0 0 20px ${color}88`,
        }}
      />
      <div
        style={{
          width: `${size * 0.18}px`,
          height: `${size * 0.18}px`,
          borderRadius: "50%",
          backgroundColor: color,
          boxShadow: `0 0 25px ${color}`,
        }}
      />
    </div>
  );
};
