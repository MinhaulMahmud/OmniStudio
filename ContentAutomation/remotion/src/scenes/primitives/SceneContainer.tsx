import React from "react";

export interface SafeZoneProps {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface SceneContainerProps {
  children: React.ReactNode;
  layoutMode?: "landscape" | "portrait" | "square";
  safeZone?: SafeZoneProps;
  backgroundColor?: string;
}

export const SceneContainer: React.FC<SceneContainerProps> = ({
  children,
  layoutMode = "landscape",
  safeZone = { top: 80, bottom: 80, left: 80, right: 80 },
  backgroundColor = "#060913",
}) => {
  return (
    <div
      style={{
        flex: 1,
        width: "100%",
        height: "100%",
        backgroundColor,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "space-between",
        boxSizing: "border-box",
        paddingTop: `${safeZone.top}px`,
        paddingBottom: `${safeZone.bottom}px`,
        paddingLeft: `${safeZone.left}px`,
        paddingRight: `${safeZone.right}px`,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {children}
    </div>
  );
};
