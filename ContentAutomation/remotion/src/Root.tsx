import React from "react";
import { Composition } from "remotion";
import { ModelWeightsComposition } from "./ModelWeightsComposition";
import { BikeGearboxComposition } from "./BikeGearboxComposition";
import { DynamicExplainer, DynamicExplainerProps } from "./DynamicExplainer";

export const Root: React.FC = () => {
  return (
    <>
      {/* 1. Custom Deep Explainer for AI Model Weights vs Compute */}
      <Composition
        id="ModelWeightsExplainer"
        component={ModelWeightsComposition}
        durationInFrames={2367} // Exactly matched to VoiceStudio narration
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          audioSrc: undefined,
        }}
      />

      {/* 2. Deep Explainer for Motorcycle Transmission & Gearbox Mechanisms */}
      <Composition
        id="BikeGearboxExplainer"
        component={BikeGearboxComposition}
        durationInFrames={1600}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          audioFile: undefined,
        }}
      />

      {/* 3. Generic Dynamic Explainer for ANY Topic / Script */}
      <Composition
        id="DynamicExplainer"
        component={DynamicExplainer}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
        calculateMetadata={({ props }) => {
          const typedProps = props as DynamicExplainerProps;
          return {
            durationInFrames: typedProps.totalFrames || 1800,
          };
        }}
        defaultProps={{
          title: "AI Model Weights Explainer",
          subtitle: "Synthesized with VoiceStudio Cloned Voice",
          category: "AI & Machine Learning",
          sections: [],
          totalFrames: 1800,
          audioFile: "narration.mp3",
        }}
      />
    </>
  );
};
