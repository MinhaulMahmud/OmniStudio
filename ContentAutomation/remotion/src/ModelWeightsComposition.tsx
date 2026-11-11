import React from "react";
import { Audio, Sequence, staticFile } from "remotion";
import { TitleScene } from "./scenes/TitleScene";
import { WeightsMatrixScene } from "./scenes/WeightsMatrixScene";
import { MemoryEquationScene } from "./scenes/MemoryEquationScene";
import { BandwidthScene } from "./scenes/BandwidthScene";
import { QuantizationScene } from "./scenes/QuantizationScene";
import { OutroScene } from "./scenes/OutroScene";

export interface CompositionProps {
  audioSrc?: string;
}

export const ModelWeightsComposition: React.FC<CompositionProps> = () => {
  return (
    <div style={{ flex: 1, backgroundColor: "#000000", position: "relative" }}>
      {/* Background Audio Narration synthesized via VoiceStudio Base TTS */}
      <Audio src={staticFile("narration.mp3")} />

      {/* Hook & Title (frame 0 -> 327) */}
      <Sequence from={0} durationInFrames={327}>
        <TitleScene />
      </Sequence>
      {/* What Are Weights? (frame 327 -> 689) */}
      <Sequence from={327} durationInFrames={362}>
        <WeightsMatrixScene />
      </Sequence>
      {/* The Memory Equation (frame 689 -> 1148) */}
      <Sequence from={689} durationInFrames={459}>
        <MemoryEquationScene />
      </Sequence>
      {/* The Bandwidth Bottleneck (frame 1148 -> 1616) */}
      <Sequence from={1148} durationInFrames={468}>
        <BandwidthScene />
      </Sequence>
      {/* Quantization Magic (frame 1616 -> 2088) */}
      <Sequence from={1616} durationInFrames={472}>
        <QuantizationScene />
      </Sequence>
      {/* Outro & Takeaways (frame 2088 -> 2367) */}
      <Sequence from={2088} durationInFrames={279}>
        <OutroScene />
      </Sequence>
    </div>
  );
};
