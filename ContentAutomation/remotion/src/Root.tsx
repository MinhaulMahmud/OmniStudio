import React from "react";
import { Composition } from "remotion";
import { DynamicExplainer } from "./DynamicExplainer";

export const Root: React.FC = () => {
  return (
    <Composition
      id="DynamicExplainer"
      component={DynamicExplainer}
      durationInFrames={1800}
      fps={30}
      width={1920}
      height={1080}
      calculateMetadata={({ props }) => {
        const typedProps = props as any;
        return {
          durationInFrames: typedProps?.totalFrames || 1800,
          width: typedProps?.width || 1920,
          height: typedProps?.height || 1080,
        };
      }}
      defaultProps={{
        title: "Dynamic Explainer",
        subtitle: "High-Quality Motion Graphics",
        category: "Technology & Science",
        sections: [],
        totalFrames: 1800,
        audioFile: "narration.mp3",
      }}
    />
  );
};
