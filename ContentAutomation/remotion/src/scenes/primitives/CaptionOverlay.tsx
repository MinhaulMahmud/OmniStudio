import React from "react";

export interface CaptionOverlayProps {
  text: string;
  accentColor?: string;
  maxWidth?: string | number;
  layoutMode?: "landscape" | "portrait" | "square";
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  text,
  accentColor = "#38bdf8",
  maxWidth,
  layoutMode = "landscape",
}) => {
  if (!text) return null;

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const bottomOffset = isPortrait ? "340px" : isSquare ? "90px" : "50px";
  const effectiveMaxWidth = maxWidth || (isPortrait ? "900px" : isSquare ? "860px" : "1400px");
  const fontSize = isPortrait ? "28px" : isSquare ? "24px" : "26px";

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomOffset,
        left: isPortrait ? "40px" : "60px",
        right: isPortrait ? "40px" : "60px",
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: effectiveMaxWidth,
          backgroundColor: "rgba(10, 15, 26, 0.88)",
          backdropFilter: "blur(14px)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "18px",
          padding: isPortrait ? "14px 28px" : "16px 36px",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontSize,
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
