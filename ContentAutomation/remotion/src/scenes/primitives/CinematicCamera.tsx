import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

export interface CinematicCameraProps {
  children: React.ReactNode;
  drift?: "zoom-in" | "zoom-out" | "pan-left" | "pan-right" | "subtle-float";
  intensity?: number; // scale delta, default 0.06
}

export const CinematicCamera: React.FC<CinematicCameraProps> = ({
  children,
  drift = "zoom-in",
  intensity = 0.06,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames || 180], [0, 1], {
    extrapolateRight: "clamp",
  });

  let scale = 1.0;
  let translateX = 0;
  let translateY = 0;

  switch (drift) {
    case "zoom-in":
      scale = 1.0 + progress * intensity;
      break;
    case "zoom-out":
      scale = 1.0 + intensity - progress * intensity;
      break;
    case "pan-left":
      scale = 1.0 + intensity * 0.5;
      translateX = -progress * 25;
      break;
    case "pan-right":
      scale = 1.0 + intensity * 0.5;
      translateX = progress * 25;
      break;
    case "subtle-float":
      scale = 1.03;
      translateX = Math.sin(frame * 0.03) * 12;
      translateY = Math.cos(frame * 0.02) * 8;
      break;
  }

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
        transformOrigin: "center center",
        position: "relative",
        willChange: "transform",
      }}
    >
      {children}
    </div>
  );
};
