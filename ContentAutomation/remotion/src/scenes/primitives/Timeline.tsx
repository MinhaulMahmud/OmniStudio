import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface TimelineStep {
  title: string;
  description?: string;
  badge?: string;
}

export interface TimelineProps {
  steps: TimelineStep[];
  activeStep?: number;
  accentColor?: string;
  width?: number | string;
}

export const Timeline: React.FC<TimelineProps> = ({
  steps,
  activeStep,
  accentColor = "#38bdf8",
  width = 950,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // If activeStep not provided, calculate from frame
  const currentStep =
    activeStep !== undefined
      ? activeStep
      : Math.min(steps.length - 1, Math.floor(frame / Math.max(1, Math.round(fps * 2.0))));

  return (
    <div
      style={{
        width,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "relative",
        padding: "30px 20px",
      }}
    >
      {/* Background Connecting Line */}
      <div
        style={{
          position: "absolute",
          top: "45px",
          left: "60px",
          right: "60px",
          height: "4px",
          backgroundColor: "rgba(255, 255, 255, 0.12)",
          borderRadius: "2px",
          zIndex: 0,
        }}
      >
        {/* Animated Active Progress Line */}
        <div
          style={{
            height: "100%",
            width: `${(currentStep / Math.max(1, steps.length - 1)) * 100}%`,
            backgroundColor: accentColor,
            boxShadow: `0 0 12px ${accentColor}`,
            transition: "width 0.3s ease",
          }}
        />
      </div>

      {steps.map((step, idx) => {
        const isActive = idx === currentStep;
        const isPast = idx < currentStep;

        return (
          <div
            key={idx}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              zIndex: 1,
              width: `${100 / steps.length}%`,
            }}
          >
            {/* Step Node Circle */}
            <div
              style={{
                width: isActive ? "42px" : "32px",
                height: isActive ? "42px" : "32px",
                borderRadius: "50%",
                backgroundColor: isActive || isPast ? accentColor : "#1e293b",
                border: `3px solid ${isActive ? "#ffffff" : isPast ? accentColor : "rgba(255,255,255,0.2)"}`,
                color: isActive || isPast ? "#0f172a" : "#94a3b8",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 800,
                fontSize: isActive ? "16px" : "13px",
                boxShadow: isActive ? `0 0 20px ${accentColor}` : "none",
                marginBottom: "14px",
                transition: "all 0.2s ease",
              }}
            >
              {idx + 1}
            </div>

            {/* Step Title */}
            <div
              style={{
                fontSize: isActive ? "18px" : "15px",
                fontWeight: isActive ? 800 : 600,
                color: isActive ? "#ffffff" : isPast ? "#cbd5e1" : "#64748b",
                marginBottom: "4px",
              }}
            >
              {step.title}
            </div>

            {/* Description */}
            {step.description && (
              <div
                style={{
                  fontSize: "13px",
                  color: isActive ? "#94a3b8" : "#475569",
                  maxWidth: "140px",
                  lineHeight: 1.3,
                }}
              >
                {step.description}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
