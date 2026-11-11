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
  layoutMode?: "landscape" | "portrait" | "square";
}

export const Timeline: React.FC<TimelineProps> = ({
  steps,
  activeStep,
  accentColor = "#38bdf8",
  width,
  layoutMode = "landscape",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const currentStep =
    activeStep !== undefined
      ? activeStep
      : Math.min(steps.length - 1, Math.floor(frame / Math.max(1, Math.round(fps * 2.0))));

  if (isPortrait) {
    // Clean Vertical Stepper for Mobile Viewports
    const effectiveWidth = width || "900px";
    return (
      <div
        style={{
          width: "100%",
          maxWidth: effectiveWidth,
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          padding: "10px 20px",
          position: "relative",
          boxSizing: "border-box",
        }}
      >
        {steps.map((step, idx) => {
          const isActive = idx <= currentStep;
          const isCurrent = idx === currentStep;
          return (
            <div
              key={idx}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "18px",
                padding: "14px 20px",
                borderRadius: "16px",
                backgroundColor: isCurrent ? "rgba(56, 189, 248, 0.15)" : "rgba(15, 23, 42, 0.7)",
                border: isCurrent ? `1.5px solid ${accentColor}` : "1px solid rgba(148, 163, 184, 0.15)",
                boxShadow: isCurrent ? `0 0 25px ${accentColor}33` : "none",
                transition: "all 0.3s ease",
              }}
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  backgroundColor: isActive ? accentColor : "#1e293b",
                  color: isActive ? "#060913" : "#64748b",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 900,
                  fontSize: "18px",
                  flexShrink: 0,
                }}
              >
                {idx + 1}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <div
                  style={{
                    color: isActive ? "#f8fafc" : "#94a3b8",
                    fontSize: "22px",
                    fontWeight: 700,
                  }}
                >
                  {step.title}
                </div>
                {step.description && (
                  <div
                    style={{
                      color: "#64748b",
                      fontSize: "18px",
                      fontWeight: 400,
                    }}
                  >
                    {step.description}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Horizontal Timeline for Landscape / Square Viewports
  const effectiveWidth = width || (isSquare ? "860px" : "1100px");
  return (
    <div
      style={{
        width: "100%",
        maxWidth: effectiveWidth,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "relative",
        padding: "30px 20px",
        boxSizing: "border-box",
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
          backgroundColor: "#1e293b",
          zIndex: 0,
        }}
      />

      {/* Animated Active Progress Line */}
      <div
        style={{
          position: "absolute",
          top: "45px",
          left: "60px",
          width: `${Math.min(100, (currentStep / Math.max(1, steps.length - 1)) * 100)}%`,
          height: "4px",
          backgroundColor: accentColor,
          boxShadow: `0 0 16px ${accentColor}`,
          zIndex: 1,
        }}
      />

      {steps.map((step, idx) => {
        const isActive = idx <= currentStep;
        const isCurrent = idx === currentStep;

        return (
          <div
            key={idx}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              zIndex: 2,
              width: "180px",
            }}
          >
            <div
              style={{
                width: isCurrent ? "44px" : "36px",
                height: isCurrent ? "44px" : "36px",
                borderRadius: "50%",
                backgroundColor: isActive ? accentColor : "#0f172a",
                border: `3px solid ${isActive ? accentColor : "#334155"}`,
                boxShadow: isCurrent ? `0 0 24px ${accentColor}` : "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: isActive ? "#060913" : "#64748b",
                fontWeight: 900,
                fontSize: "18px",
                marginBottom: "12px",
              }}
            >
              {idx + 1}
            </div>
            <div
              style={{
                color: isActive ? "#f8fafc" : "#64748b",
                fontSize: "20px",
                fontWeight: 700,
                marginBottom: "4px",
                lineHeight: 1.2,
              }}
            >
              {step.title}
            </div>
            {step.description && (
              <div
                style={{
                  color: "#94a3b8",
                  fontSize: "14px",
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
