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
}

export const DiagramNodes: React.FC<DiagramNodesProps> = ({
  nodes,
  edges = [],
  width = 900,
  height = 420,
  title,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: "rgba(11, 15, 25, 0.9)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "20px",
        padding: "20px",
        boxShadow: "0 15px 35px rgba(0, 0, 0, 0.6)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {title && (
        <div style={{ fontSize: "16px", fontWeight: 800, color: "#94a3b8", letterSpacing: "1px", textTransform: "uppercase", marginBottom: "8px" }}>
          {title}
        </div>
      )}
      <svg viewBox="0 0 1000 500" style={{ width: "100%", height: "100%" }}>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 9 5 L 0 9 z" fill="#38bdf8" />
          </marker>
        </defs>

        {/* Connecting Edges */}
        {edges.map((edge, idx) => {
          const fromNode = nodeMap.get(edge.from);
          const toNode = nodeMap.get(edge.to);
          if (!fromNode || !toNode) return null;

          const x1 = (fromNode.x / 100) * 1000;
          const y1 = (fromNode.y / 100) * 500;
          const x2 = (toNode.x / 100) * 1000;
          const y2 = (toNode.y / 100) * 500;

          const pulseOffset = (frame * 5 + idx * 30) % 100;

          return (
            <g key={idx}>
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="rgba(56, 189, 248, 0.3)"
                strokeWidth="2.5"
                strokeDasharray="6 4"
                markerEnd="url(#arrow)"
              />
              {/* Animated Signal Particle */}
              <circle
                cx={x1 + ((x2 - x1) * pulseOffset) / 100}
                cy={y1 + ((y2 - y1) * pulseOffset) / 100}
                r="4"
                fill="#38bdf8"
                filter="drop-shadow(0 0 6px #38bdf8)"
              />
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node, idx) => {
          const nx = (node.x / 100) * 1000;
          const ny = (node.y / 100) * 500;
          const nodeColor = node.color || "#38bdf8";

          const nodeScale = interpolate(frame, [idx * 8, idx * 8 + 15], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <g key={node.id} transform={`translate(${nx}, ${ny}) scale(${nodeScale})`}>
              <rect
                x="-85"
                y="-35"
                width="170"
                height="70"
                rx="14"
                fill="#0f172a"
                stroke={nodeColor}
                strokeWidth="2"
                filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))"
              />
              <text
                x="0"
                y={node.sub ? "-4" : "6"}
                textAnchor="middle"
                fill="#ffffff"
                fontSize="15"
                fontWeight="700"
              >
                {node.label}
              </text>
              {node.sub && (
                <text x="0" y="16" textAnchor="middle" fill="#94a3b8" fontSize="12">
                  {node.sub}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
};
