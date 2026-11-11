import React from "react";
import { Audio, Sequence, staticFile } from "remotion";
import { EngineExteriorScene } from "./scenes/gearbox/EngineExteriorScene";
import { EngineZoomInsideScene } from "./scenes/gearbox/EngineZoomInsideScene";
import { ConstantMeshMechanismScene } from "./scenes/gearbox/ConstantMeshMechanismScene";
import { ShiftingAndRatiosScene } from "./scenes/gearbox/ShiftingAndRatiosScene";

export interface BikeGearboxCompositionProps {
  audioFile?: string;
}

export const BikeGearboxComposition: React.FC<BikeGearboxCompositionProps> = ({
  audioFile,
}) => {
  return (
    <div style={{ flex: 1, backgroundColor: "#000000", position: "relative" }}>
      {/* Optional Audio Narration track if provided */}
      {audioFile && <Audio src={staticFile(audioFile)} />}

      {/* 1. Engine Exterior & 4-Stroke Combustion (frame 0 -> 240, ~8s) */}
      <Sequence from={0} durationInFrames={240}>
        <EngineExteriorScene />
      </Sequence>

      {/* 2. Zoom In: Penetrating inside the Casing (frame 240 -> 540, ~10s) */}
      <Sequence from={240} durationInFrames={300}>
        <EngineZoomInsideScene />
      </Sequence>

      {/* 3. Constant Mesh 6-Speed Animated Mechanism (frame 540 -> 1140, ~20s) */}
      <Sequence from={540} durationInFrames={600}>
        <ConstantMeshMechanismScene />
      </Sequence>

      {/* 4. Gear Ratios & Torque Multiplication Breakdown (frame 1140 -> 1600, ~15s) */}
      <Sequence from={1140} durationInFrames={460}>
        <ShiftingAndRatiosScene />
      </Sequence>
    </div>
  );
};
