"use client";
import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLLUTANT_META } from "@/lib/constants";
import "leaflet/dist/leaflet.css";

// Fix Leaflet marker icons
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import { Icon } from "leaflet";

interface Props {
  records: AirRecord[];
  pollutant?: keyof typeof POLLUTANT_META;
}

// Coordonnées de Cotonou, Bénin
const COTONOU_LAT = 6.3654;
const COTONOU_LON = 2.4505;

// Marker personnalisé avec couleur dynamique
const createCustomMarker = (color: string, size: number) => {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      background-color: ${color};
      border: 2px solid white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      color: white;
      font-weight: bold;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
      position: relative;
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

export default function MapChart({ records, pollutant = "pm2_5" }: Props) {
  const [selectedMarker, setSelectedMarker] = useState<AirRecord | null>(null);

  const meta = POLLUTANT_META[pollutant] || { label: pollutant, unit: "", color: COLORS.muted };

  // Get latest records with location data
  const latestRecords = records
    .filter((r) => r.lat && r.lon && !isNaN(r[pollutant] as number))
    .slice(-100);

  // Normalize values for color and size
  const values = latestRecords.map((r) => r[pollutant] as number).filter((v) => !isNaN(v));
  const minVal = values.length > 0 ? Math.min(...values) : 0;
  const maxVal = values.length > 0 ? Math.max(...values) : 1;
  const normalize = (v: number) => (maxVal > minVal ? (v - minVal) / (maxVal - minVal) : 0.5);

  const getMarkerColor = (value: number) => {
    const t = normalize(value);
    // Red scale: from light to dark red
    const r = Math.round(255);
    const g = Math.round(100 - t * 100);
    const b = Math.round(100 - t * 100);
    return `rgb(${r},${g},${b})`;
  };

  const getMarkerSize = (value: number) => {
    const t = normalize(value);
    return 20 + t * 30; // Size between 20 and 50
  };

  return (
    <div style={{ height: 400, borderRadius: 8, overflow: "hidden", border: `1px solid ${COLORS.border}`, position: "relative" }}>
      <MapContainer center={[COTONOU_LAT, COTONOU_LON]} zoom={11} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />

        {/* Markers for each record */}
        {latestRecords.map((record, idx) => {
          const value = record[pollutant] as number;
          const markerColor = getMarkerColor(value);
          const markerSize = getMarkerSize(value);
          const lat = typeof record.lat === 'number' ? record.lat : parseFloat(record.lat as any);
          const lon = typeof record.lon === 'number' ? record.lon : parseFloat(record.lon as any);

          return (
            <Marker 
              key={idx} 
              position={[lat, lon]} 
              icon={createCustomMarker(markerColor, markerSize)}
              eventHandlers={{
                click: () => setSelectedMarker(record),
              }}
            >
              <Popup>
                <div style={{ padding: 8, minWidth: 200, fontSize: 12 }}>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>
                    {meta.label}
                  </div>
                  <div style={{ fontSize: 14, marginBottom: 6 }}>
                    <strong>{(value).toFixed(2)}</strong> {meta.unit}
                  </div>
                  <div style={{ fontSize: 11, color: "#666" }}>
                    📅 {record.date}
                  </div>
                  {lat && lon && (
                    <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>
                      📍 {lat.toFixed(4)}°, {lon.toFixed(4)}°
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Legend */}
      <div style={{
        position: "absolute",
        bottom: 16,
        left: 16,
        background: COLORS.surface,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 8,
        padding: 12,
        fontSize: 11,
        color: COLORS.border,
        fontFamily: "JetBrains Mono, monospace",
        maxWidth: 200,
        zIndex: 1000,
      }}>
        <div style={{ marginBottom: 8, fontWeight: 600 }}>Légende</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <div style={{ width: 20, height: 20, borderRadius: "50%", backgroundColor: "rgb(255, 100, 100)", border: "2px solid white" }} />
          <span>Faible</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 30, height: 30, borderRadius: "50%", backgroundColor: "rgb(255, 0, 0)", border: "2px solid white" }} />
          <span>Élevé</span>
        </div>
      </div>

      {/* Attribution pour OpenStreetMap */}
      <div style={{
        position: "absolute",
        bottom: 0,
        right: 0,
        fontSize: 10,
        background: "rgba(0,0,0,0.5)",
        color: "white",
        padding: "4px 8px",
        zIndex: 999,
      }}>
        © OpenStreetMap
      </div>
    </div>
  );
}
