import React from "react";

export interface CaptionOverlayProps {
  text: string;
  accentColor?: string;
  maxWidth?: string | number;
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  text,
  accentColor = "#38bdf8",
  maxWidth = 1400,
}) => {
  if (!text) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "40px",
        left: "60px",
        right: "60px",
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth,
          backgroundColor: "rgba(10, 15, 26, 0.88)",
          backdropFilter: "blur(14px)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "18px",
          padding: "16px 36px",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontSize: "24px",
            lineHeight: 1.4,
            fontWeight: 600,
            color: "#f8fafc",
            textShadow: "0 2px 4px rgba(0,0,0,0.8)",
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};
