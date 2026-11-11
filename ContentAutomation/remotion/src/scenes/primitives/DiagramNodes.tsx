import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface DiagramNode {
  id: string;
  label: string;
  sub?: string;
  x: number; // 0 to 100 percentage
  y: number; // 0 to 100 percentage
  color?: string;
}

export interface DiagramEdge {
  from: string;
  to: string;
  label?: string;
}

export interface DiagramNodesProps {
  nodes: DiagramNode[];
  edges?: DiagramEdge[];
  width?: number | string;
  height?: number;
  title?: string;
  layoutMode?: "landscape" | "portrait" | "square";
}

export const DiagramNodes: React.FC<DiagramNodesProps> = ({
  nodes,
  edges = [],
  width,
  height,
  title,
  layoutMode = "landscape",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isPortrait = layoutMode === "portrait";
  const isSquare = layoutMode === "square";

  const effectiveWidth = width || (isPortrait ? "900px" : isSquare ? "860px" : "1000px");
  const effectiveHeight = height || (isPortrait ? 500 : isSquare ? 420 : 420);

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div
      style={{
        width: "100%",
        maxWidth: effectiveWidth,
        height: effectiveHeight,
        backgroundColor: "rgba(11, 15, 25, 0.9)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: "20px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.6)",
        position: "relative",
        overflow: "hidden",
        boxSizing: "border-box",
      }}
    >
      {title && (
        <div
          style={{
            color: "#38bdf8",
            fontSize: isPortrait ? "20px" : "18px",
            fontWeight: 800,
            textTransform: "uppercase",
            letterSpacing: "1px",
            marginBottom: "10px",
          }}
        >
          {title}
        </div>
      )}

      {/* SVG Connecting Edges */}
      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
          </marker>
        </defs>

        {edges.map((edge, i) => {
          const fromNode = nodeMap.get(edge.from);
          const toNode = nodeMap.get(edge.to);
          if (!fromNode || !toNode) return null;

          return (
            <line
              key={i}
              x1={`${fromNode.x}%`}
              y1={`${fromNode.y}%`}
              x2={`${toNode.x}%`}
              y2={`${toNode.y}%`}
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeDasharray="6 4"
              opacity="0.75"
              markerEnd="url(#arrow)"
            />
          );
        })}
      </svg>

      {/* Nodes */}
      {nodes.map((node, i) => {
        const nodeColor = node.color || "#38bdf8";
        const delay = i * 6;
        const opacity = interpolate(frame, [delay, delay + 15], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={node.id}
            style={{
              position: "absolute",
              left: `${node.x}%`,
              top: `${node.y}%`,
              transform: "translate(-50%, -50%)",
              backgroundColor: "rgba(15, 23, 42, 0.95)",
              border: `2px solid ${nodeColor}`,
              borderRadius: "14px",
              padding: isPortrait ? "10px 16px" : "8px 16px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              boxShadow: `0 0 20px ${nodeColor}33`,
              opacity,
              zIndex: 2,
              minWidth: isPortrait ? "120px" : "100px",
            }}
          >
            <span
              style={{
                color: "#f8fafc",
                fontSize: isPortrait ? "16px" : "15px",
                fontWeight: 700,
                textAlign: "center",
                whiteSpace: "nowrap",
              }}
            >
              {node.label}
            </span>
            {node.sub && (
              <span
                style={{
                  color: "#94a3b8",
                  fontSize: isPortrait ? "13px" : "12px",
                  marginTop: "2px",
                  textAlign: "center",
                  whiteSpace: "nowrap",
                }}
              >
                {node.sub}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};
