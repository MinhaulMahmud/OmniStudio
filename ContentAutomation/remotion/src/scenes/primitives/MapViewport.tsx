import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import {
  geoEqualEarth,
  geoMercator,
  geoOrthographic,
  geoPath,
  geoInterpolate,
} from "d3-geo";
import * as topojson from "topojson-client";
import worldData from "../../assets/maps/world-110m.json";

export interface HighlightCountry {
  id: string; // Country name or ISO ID (e.g. 'Italy', 'Egypt', 'China', 'USA', '380')
  label?: string;
  color?: string; // Default cyan/amber
  appearAtFrame?: number;
}

export interface MapArc {
  from: [number, number]; // [lng, lat]
  to: [number, number]; // [lng, lat]
  label?: string;
  color?: string;
  appearAtFrame?: number;
  drawDurationFrames?: number;
}

export interface MapPin {
  lngLat: [number, number]; // [lng, lat]
  label: string;
  color?: string;
  appearAtFrame?: number;
}

export interface MapViewportProps {
  projectionType?: "equal-earth" | "mercator" | "orthographic";
  center?: [number, number]; // [lng, lat] focus center
  zoom?: number; // scale multiplier (default 1.0)
  rotate?: [number, number, number]; // for orthographic globe rotation
  highlightCountries?: HighlightCountry[];
  arcs?: MapArc[];
  pins?: MapPin[];
  width?: number;
  height?: number;
  theme?: "cyber" | "dark-slate" | "vintage";
}

export const MapViewport: React.FC<MapViewportProps> = ({
  projectionType = "equal-earth",
  center = [0, 20],
  zoom = 1.0,
  rotate = [0, 0, 0],
  highlightCountries = [],
  arcs = [],
  pins = [],
  width: customWidth,
  height: customHeight,
  theme = "cyber",
}) => {
  const frame = useCurrentFrame();
  const { width: configWidth, height: configHeight, fps, durationInFrames } = useVideoConfig();

  const width = customWidth || configWidth;
  const height = customHeight || configHeight;

  // Extract TopoJSON country features
  const countriesGeo = useMemo(() => {
    const rawData = worldData as any;
    return topojson.feature(rawData, rawData.objects.countries) as any;
  }, []);

  // Theme palettes
  const palette = {
    cyber: {
      sea: "#060913",
      land: "#111827",
      border: "#1f2937",
      grid: "rgba(0, 229, 255, 0.08)",
      defaultHighlight: "#00e5ff",
      defaultArc: "#38bdf8",
      defaultPin: "#f59e0b",
    },
    "dark-slate": {
      sea: "#080c16",
      land: "#1e293b",
      border: "#334155",
      grid: "rgba(255, 255, 255, 0.04)",
      defaultHighlight: "#38bdf8",
      defaultArc: "#818cf8",
      defaultPin: "#10b981",
    },
    vintage: {
      sea: "#0f172a",
      land: "#334155",
      border: "#475569",
      grid: "rgba(245, 158, 11, 0.05)",
      defaultHighlight: "#f59e0b",
      defaultArc: "#ec4899",
      defaultPin: "#38bdf8",
    },
  }[theme];

  // Subtle continuous camera drift
  const cameraDrift = interpolate(frame, [0, durationInFrames || 180], [1.0, 1.04], {
    extrapolateRight: "clamp",
  });
  const currentZoom = zoom * cameraDrift;

  // Setup d3-geo projection
  const projection = useMemo(() => {
    let proj: any;
    const baseScale = width / 6.2 * currentZoom;

    if (projectionType === "orthographic") {
      proj = geoOrthographic()
        .scale(baseScale * 1.3)
        .translate([width / 2, height / 2])
        .rotate([rotate[0] + frame * 0.2, rotate[1], rotate[2]]);
    } else if (projectionType === "mercator") {
      proj = geoMercator()
        .scale(baseScale)
        .center(center)
        .translate([width / 2, height / 2]);
    } else {
      proj = geoEqualEarth()
        .scale(baseScale * 1.1)
        .center(center)
        .translate([width / 2, height / 2]);
    }
    return proj;
  }, [projectionType, currentZoom, center, rotate, width, height, frame]);

  const pathGenerator = useMemo(() => geoPath().projection(projection), [projection]);

  // Pre-process highlight match lookup
  const highlightMap = useMemo(() => {
    const map = new Map<string, HighlightCountry>();
    for (const h of highlightCountries) {
      map.set(h.id.toLowerCase().trim(), h);
    }
    return map;
  }, [highlightCountries]);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: palette.sea,
        }}
      >
        <defs>
          <filter id="arcGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#00e5ff" floodOpacity="0.8" />
          </filter>
          <filter id="countryGlow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="0" stdDeviation="6" floodColor="#00e5ff" floodOpacity="0.6" />
          </filter>
        </defs>

        {/* 1. Base Map: Countries */}
        <g>
          {countriesGeo.features.map((feature: any, idx: number) => {
            const name = (feature.properties?.name || "").toLowerCase().trim();
            const idStr = String(feature.id || "").toLowerCase().trim();

            // Check if this country is highlighted
            const highlightConfig =
              highlightMap.get(name) ||
              highlightMap.get(idStr) ||
              Array.from(highlightMap.values()).find(
                (h) => name.includes(h.id.toLowerCase()) || idStr === h.id.toLowerCase()
              );

            let fill = palette.land;
            let stroke = palette.border;
            let strokeWidth = 0.8;
            let filter: string | undefined = undefined;

            if (highlightConfig) {
              const startF = highlightConfig.appearAtFrame || 0;
              const hFrame = frame - startF;
              const hOpacity = interpolate(hFrame, [0, 15], [0, 0.75], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });

              const hColor = highlightConfig.color || palette.defaultHighlight;
              fill = hColor;
              stroke = hColor;
              strokeWidth = 2.0;
              filter = "url(#countryGlow)";

              return (
                <path
                  key={feature.id || idx}
                  d={pathGenerator(feature) || ""}
                  fill={fill}
                  fillOpacity={hOpacity}
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                  filter={filter}
                />
              );
            }

            return (
              <path
                key={feature.id || idx}
                d={pathGenerator(feature) || ""}
                fill={fill}
                stroke={stroke}
                strokeWidth={strokeWidth}
              />
            );
          })}
        </g>

        {/* 2. Great-Circle Arcs */}
        <g>
          {arcs.map((arc, i) => {
            const startF = arc.appearAtFrame || 0;
            const drawDuration = arc.drawDurationFrames || 45;
            const arcFrame = frame - startF;

            const progress = interpolate(arcFrame, [0, drawDuration], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });

            if (progress <= 0) return null;

            // Generate great-circle line string using d3-geo interpolation
            const interpolator = geoInterpolate(arc.from, arc.to);
            const numSteps = 40;
            const currentSteps = Math.max(2, Math.floor(progress * numSteps));
            const arcCoords = Array.from({ length: currentSteps }, (_, s) =>
              interpolator(s / (numSteps - 1))
            );

            const arcLineString: any = {
              type: "LineString",
              coordinates: arcCoords,
            };

            const pathD = pathGenerator(arcLineString) || "";
            const arcColor = arc.color || palette.defaultArc;

            return (
              <g key={i}>
                <path
                  d={pathD}
                  fill="none"
                  stroke={arcColor}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  filter="url(#arcGlow)"
                />
                {/* Traveling pulse head */}
                {arcCoords.length > 0 && (() => {
                  const headCoord = arcCoords[arcCoords.length - 1];
                  const projected = projection(headCoord);
                  if (!projected) return null;
                  return (
                    <circle
                      cx={projected[0]}
                      cy={projected[1]}
                      r={5}
                      fill="#ffffff"
                      filter="url(#arcGlow)"
                    />
                  );
                })()}
              </g>
            );
          })}
        </g>

        {/* 3. Coordinate Pins & Radar Rings */}
        <g>
          {pins.map((pin, i) => {
            const startF = pin.appearAtFrame || 0;
            const pinFrame = frame - startF;

            const scale = spring({
              frame: pinFrame,
              fps,
              config: { damping: 10, stiffness: 240, mass: 0.6 },
            });

            if (pinFrame < 0) return null;

            const projected = projection(pin.lngLat);
            if (!projected) return null;
            const [px, py] = projected;

            const pinColor = pin.color || palette.defaultPin;
            const rippleProgress = (pinFrame % 30) / 30;
            const rippleR = interpolate(rippleProgress, [0, 1], [6, 24]);
            const rippleOpacity = interpolate(rippleProgress, [0, 1], [0.8, 0]);

            return (
              <g key={i} transform={`translate(${px}, ${py})`}>
                {/* Expanding radar ring */}
                <circle
                  cx={0}
                  cy={0}
                  r={rippleR}
                  fill="none"
                  stroke={pinColor}
                  strokeWidth="1.5"
                  opacity={rippleOpacity}
                />
                {/* Solid center dot */}
                <circle
                  cx={0}
                  cy={0}
                  r={6}
                  fill={pinColor}
                  transform={`scale(${Math.max(0, scale)})`}
                  style={{ transformOrigin: "0 0" }}
                />
                {/* Pin label */}
                {pin.label && (
                  <text
                    x={0}
                    y={-14}
                    fill="#ffffff"
                    fontSize="13"
                    fontWeight="700"
                    fontFamily="'JetBrains Mono', monospace, sans-serif"
                    textAnchor="middle"
                    style={{
                      textShadow: "0 2px 6px rgba(0,0,0,0.9)",
                    }}
                  >
                    {pin.label}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
};
