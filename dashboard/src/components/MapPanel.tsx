import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { IncidentState } from "../types/incident";

interface MapPanelProps {
  incident: IncidentState | null;
}

function tempToColor(temp: number, alpha = 0.55): string {
  const minT = 28, maxT = 50;
  const t = Math.max(0, Math.min(1, (temp - minT) / (maxT - minT)));
  const hue = Math.round(180 - t * 180);
  return `hsla(${hue}, 90%, 55%, ${alpha})`;
}

function addRouteLayer(map: maplibregl.Map, id: string, geometry: any, color: string) {
  if (!geometry) return;
  if (map.getLayer(id)) map.removeLayer(id);
  if (map.getSource(id)) map.removeSource(id);
  map.addSource(id, { type: "geojson", data: { type: "Feature", geometry, properties: {} } });
  map.addLayer({ id, type: "line", source: id, paint: { "line-color": color, "line-width": 3, "line-opacity": 0.85, "line-dasharray": [2, 1] } });
}

function addFacilityMarker(map: maplibregl.Map, lat: number, lon: number, emoji: string, name: string, color: string) {
  const el = document.createElement("div");
  el.style.cssText = `font-size:20px;cursor:pointer;filter:drop-shadow(0 2px 6px ${color});`;
  el.textContent = emoji;
  el.title = name;
  new maplibregl.Marker({ element: el })
    .setLngLat([lon, lat])
    .setPopup(
      new maplibregl.Popup({ closeButton: false }).setHTML(
        `<div style="font-family:Inter,sans-serif;font-size:12px;color:#e8f0fe">
          <div style="font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:#4d6080;margin-bottom:3px">${name.split(" ")[0]}</div>
          <div style="font-weight:600">${name}</div>
        </div>`
      )
    )
    .addTo(map);
}

export const MapPanel: React.FC<MapPanelProps> = ({ incident }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const [ready, setReady] = useState(false);

  const lastObs = incident?.observations?.[incident.observations.length - 1];
  const lat = lastObs?.location.latitude ?? 26.9124;
  const lon = lastObs?.location.longitude ?? 75.7873;
  const address = lastObs?.location.address || "Monitoring Site";

  const events = incident?.events || [];
  const hasFire = events.some(e => e.event_type === "possible_fire" && e.status === "likely");
  const hasBlock = events.some(e => e.event_type === "road_block");

  const fgObs = incident?.observations?.find(o => o.source === "FortyGuard" && o.raw_payload);
  const heatmapGeoJSON = fgObs?.raw_payload as any | null;

  // Extract routes and facility data from action proposal
  const responderAction = incident?.action_proposal?.actions?.find(a => a.type === "responder_guidance");
  const civilianAction = incident?.action_proposal?.actions?.find(a => a.type === "civilian_alert");

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://tiles.openfreemap.org/styles/dark",
      center: [lon, lat],
      zoom: 13.5,
      pitch: 20,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

    // Suppress missing sprite image warnings (wood-pattern etc.)
    map.on("styleimagemissing", (e) => {
      if (!map.hasImage(e.id)) {
        const canvas = document.createElement("canvas");
        canvas.width = 1; canvas.height = 1;
        const ctx = canvas.getContext("2d");
        if (ctx) { ctx.fillStyle = "transparent"; ctx.fillRect(0, 0, 1, 1); }
        map.addImage(e.id, { width: 1, height: 1, data: new Uint8Array(4) });
      }
    });

    const el = document.createElement("div");
    el.setAttribute("role", "img");
    el.setAttribute("aria-label", "Map marker");
    el.style.cssText = "width:14px;height:14px;border-radius:50%;background:#22d3ee;border:2px solid #fff;box-shadow:0 0 0 4px rgba(34,211,238,0.25),0 0 20px rgba(34,211,238,0.4);";
    const marker = new maplibregl.Marker({ element: el }).setLngLat([lon, lat]).addTo(map);

    mapRef.current = map;
    markerRef.current = marker;
    map.on("load", () => setReady(true));

    // Debounced ResizeObserver — prevents MapLibre layout thrashing
    // _updateCompact and _containerDimensions query geometry after DOM mutations
    let resizeTimer: ReturnType<typeof setTimeout>;
    const ro = new ResizeObserver(() => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => { map.resize(); }, 150);
    });
    if (containerRef.current) ro.observe(containerRef.current);

    return () => {
      clearTimeout(resizeTimer);
      ro.disconnect();
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
      setReady(false);
    };
  }, []);

  // Fly to new location
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    map.flyTo({ center: [lon, lat], zoom: 13.5, speed: 1.2, essential: true });
    markerRef.current?.setLngLat([lon, lat]);
  }, [lat, lon, ready]);

  // FortyGuard heatmap tiles
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    ["fg-heat-fill", "fg-heat-outline"].forEach(id => { if (map.getLayer(id)) map.removeLayer(id); });
    if (map.getSource("fg-heat")) map.removeSource("fg-heat");
    if (!heatmapGeoJSON?.features?.length) return;
    const colored = {
      type: "FeatureCollection" as const,
      features: heatmapGeoJSON.features.map((f: any) => ({
        ...f,
        properties: {
          ...f.properties,
          fill_color: tempToColor(f.properties.average_temperature ?? 30, 0.55),
          stroke_color: tempToColor(f.properties.average_temperature ?? 30, 0.85),
          temp: f.properties.average_temperature ?? 0,
        },
      })),
    };
    map.addSource("fg-heat", { type: "geojson", data: colored });
    map.addLayer({ id: "fg-heat-fill", type: "fill", source: "fg-heat", paint: { "fill-color": ["get", "fill_color"], "fill-opacity": 0.7 } });
    map.addLayer({ id: "fg-heat-outline", type: "line", source: "fg-heat", paint: { "line-color": ["get", "stroke_color"], "line-width": 0.5, "line-opacity": 0.5 } });
    map.on("click", "fg-heat-fill", (e) => {
      const f = e.features?.[0];
      if (!f) return;
      const t = f.properties.temp;
      new maplibregl.Popup({ closeButton: false }).setLngLat(e.lngLat).setHTML(`
        <div style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#e8f0fe">
          <div style="font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:#4d6080;margin-bottom:4px">FortyGuard Tile</div>
          <div style="font-size:20px;font-weight:700;color:${tempToColor(t, 1)}">${Number(t).toFixed(1)}°C</div>
          <div style="font-size:10px;color:#8ba3cc;margin-top:4px">Tile ID: ${f.properties.tile_id ?? "—"}</div>
        </div>`).addTo(map);
    });
    map.on("mouseenter", "fg-heat-fill", () => { map.getCanvas().style.cursor = "crosshair"; });
    map.on("mouseleave", "fg-heat-fill", () => { map.getCanvas().style.cursor = ""; });
  }, [heatmapGeoJSON, ready]);

  // Facility routes + markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    // Hospital route (blue)
    const hospitalRoute = civilianAction?.details?.hospital_route || responderAction?.details?.hospital?.route_geojson;
    const hospitalCoords = civilianAction?.details?.hospital_coords || responderAction?.details?.hospital;
    addRouteLayer(map, "route-hospital", hospitalRoute, "#3b82f6");
    if (hospitalCoords?.lat) {
      addFacilityMarker(map, hospitalCoords.lat, hospitalCoords.lon, "🏥", responderAction?.details?.hospital?.name || "Hospital", "#3b82f6");
    }

    // Fire station route (red)
    const fireRoute = responderAction?.details?.fire_station?.route_geojson;
    const fireCoords = responderAction?.details?.fire_station;
    addRouteLayer(map, "route-firestation", fireRoute, "#ef4444");
    if (fireCoords?.lat) {
      addFacilityMarker(map, fireCoords.lat, fireCoords.lon, "🚒", fireCoords.name || "Fire Station", "#ef4444");
    }

    // Cooling center route (cyan)
    const coolingRoute = civilianAction?.details?.cooling_center_route;
    const coolingCoords = civilianAction?.details?.cooling_center_coords;
    addRouteLayer(map, "route-cooling", coolingRoute, "#22d3ee");
    if (coolingCoords?.lat) {
      addFacilityMarker(map, coolingCoords.lat, coolingCoords.lon, "❄️", civilianAction?.details?.cooling_center || "Cooling Center", "#22d3ee");
    }
  }, [responderAction, civilianAction, ready]);

  // Fire/blockage markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (hasFire && lat && lon) {
      const el = document.createElement("div");
      el.innerHTML = "🔥";
      el.style.cssText = "font-size:22px;filter:drop-shadow(0 0 8px #ef4444);";
      new maplibregl.Marker({ element: el }).setLngLat([lon, lat]).addTo(map);
    }
    if (hasBlock && lat && lon) {
      const el = document.createElement("div");
      el.innerHTML = "🚧";
      el.style.cssText = "font-size:18px;filter:drop-shadow(0 0 6px #f97316);";
      new maplibregl.Marker({ element: el }).setLngLat([lon + 0.002, lat - 0.001]).addTo(map);
    }
  }, [hasFire, hasBlock, lat, lon, ready]);

  const fgMode = fgObs ? (fgObs.data_mode?.toUpperCase() ?? "—") : null;
  const hasHospitalRoute = !!(civilianAction?.details?.hospital_route || responderAction?.details?.hospital?.route_geojson);
  const hasFireRoute = !!responderAction?.details?.fire_station?.route_geojson;

  return (
    <div className="card map-panel">
      <div className="map-header">
        <span className="map-title">Live Operational Map</span>
        <div className="map-legend">
          {fgMode && <span className="legend-item"><span className="legend-dot" style={{ background: "#22d3ee" }} />FortyGuard {fgMode}</span>}
          {hasFire && <span className="legend-item"><span className="legend-dot" style={{ background: "#ef4444" }} />Fire Zone</span>}
          {hasFireRoute && <span className="legend-item"><span className="legend-dot" style={{ background: "#ef4444", opacity: 0.7 }} />🚒 Route</span>}
          {hasHospitalRoute && <span className="legend-item"><span className="legend-dot" style={{ background: "#3b82f6", opacity: 0.7 }} />🏥 Route</span>}
          {hasBlock && <span className="legend-item"><span className="legend-dot" style={{ background: "#f97316" }} />Road Block</span>}
        </div>
      </div>
      <div className="map-canvas">
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
        {!ready && (
          <div className="map-loader">
            <div className="replan-spinner" />
            <span style={{ fontSize: 11 }}>Loading OpenFreeMap vector tiles…</span>
          </div>
        )}
      </div>
      <div className="map-footer">
        <span>📍 {lat.toFixed(5)}°N, {lon.toFixed(5)}°E</span>
        <span style={{ maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{address}</span>
        {heatmapGeoJSON && <span style={{ color: "#22d3ee" }}>{heatmapGeoJSON.features?.length ?? 0} heat tiles</span>}
      </div>
    </div>
  );
};
