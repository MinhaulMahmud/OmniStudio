"""
Tests for Feature C: Map Animation Capability (d3-geo + TopoJSON)
================================================================
Covers:
  - world-110m.json TopoJSON asset existence & schema validation
  - MapViewport primitive implementation and exports
  - Geographic context detection in VisualMechanismViewport
  - Validation rules compatibility with MapViewport
"""
import json
import pytest
from pathlib import Path
from validate_scene import validate_scene_code


def test_world_topojson_asset_exists_and_valid():
    """Verify that world-110m.json exists, is valid JSON, and has TopoJSON objects.countries."""
    asset_path = Path(__file__).resolve().parent.parent / "remotion" / "src" / "assets" / "maps" / "world-110m.json"
    assert asset_path.exists(), f"Missing TopoJSON asset: {asset_path}"

    with open(asset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("type") == "Topology"
    assert "objects" in data
    assert "countries" in data["objects"]
    assert len(data["objects"]["countries"]["geometries"]) > 100


def test_map_viewport_primitive_exported():
    """Verify MapViewport is exported from primitives/index.ts."""
    index_path = Path(__file__).resolve().parent.parent / "remotion" / "src" / "scenes" / "primitives" / "index.ts"
    content = index_path.read_text(encoding="utf-8")
    assert 'export * from "./MapViewport";' in content


def test_validate_scene_accepts_map_viewport():
    """Verify that an AST containing MapViewport passes scene validation cleanly."""
    map_code = """
    import React from "react";
    import { useCurrentFrame, interpolate } from "remotion";
    import { MapViewport, CinematicCamera, DynamicBackdrop } from "../primitives";

    export const MapScene: React.FC = () => {
        const frame = useCurrentFrame();
        const zoom = interpolate(frame, [0, 90], [1.0, 1.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
            <CinematicCamera drift="zoom-in">
                <DynamicBackdrop theme="dark-slate" />
                <MapViewport
                    projectionType="equal-earth"
                    zoom={zoom}
                    highlightCountries={[{ id: "Italy", appearAtFrame: 0 }]}
                    pins={[{ lngLat: [12.49, 41.90], label: "Rome", appearAtFrame: 5 }]}
                    arcs={[{ from: [12.49, 41.90], to: [28.97, 41.00], appearAtFrame: 10 }]}
                />
            </CinematicCamera>
        );
    };
    """
    violations = validate_scene_code(map_code)
    assert len(violations) == 0, f"Unexpected violations: {violations}"


def test_visual_mechanism_has_geographic_branch():
    """Verify VisualMechanismViewport detects geographic topics and routes to MapViewport."""
    viewport_path = Path(__file__).resolve().parent.parent / "remotion" / "src" / "components" / "VisualMechanismViewport.tsx"
    content = viewport_path.read_text(encoding="utf-8")

    assert "isGeographic" in content
    assert "MapViewport" in content
    assert "silk road" in content
    assert "trade" in content
