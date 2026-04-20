"use client";
import { useState, useEffect } from "react";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLLUTANT_META } from "@/lib/constants";

/* ── Leaflet est chargé côté client uniquement (incompatible SSR) ── */
let MapContainer: any, TileLayer: any, Marker: any, Popup: any, L: any;

interface Props {
  records: AirRecord[];
  pollutant?: keyof typeof POLLUTANT_META;
}

const COTONOU_LAT = 6.3654;
const COTONOU_LON = 2.4505;

/* Échelle de couleur : vert → jaune → orange → rouge */
function pollutantColor(t: number): string {
  if (t < 0.33) {
    // teal → amber
    const r = Math.round(0   + t * 3 * (245 - 0));
    const g = Math.round(196 + t * 3 * (158 - 196));
    const b = Math.round(154 + t * 3 * (11  - 154));
    return `rgb(${r},${g},${b})`;
  } else if (t < 0.66) {
    // amber → coral
    const s = (t - 0.33) * 3;
    const r = Math.round(245 + s * (249 - 245));
    const g = Math.round(158 + s * (115 - 158));
    const b = Math.round(11  + s * (22  - 11));
    return `rgb(${r},${g},${b})`;
  } else {
    // coral → danger
    const s = (t - 0.66) * 3;
    const r = Math.round(249 + s * (239 - 249));
    const g = Math.round(115 + s * (68  - 115));
    const b = Math.round(22  + s * (68  - 22));
    return `rgb(${r},${g},${b})`;
  }
}

function createMarker(color: string, size: number) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:${size}px; height:${size}px;
      border-radius:50%;
      background:${color};
      border:2.5px solid rgba(255,255,255,0.85);
      box-shadow:0 2px 10px rgba(0,0,0,0.35);
      cursor:pointer;
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

/* Échelle de légende */
const LEGEND_STOPS = [
  { label: "Faible",    t: 0,    color: pollutantColor(0) },
  { label: "Modéré",   t: 0.33, color: pollutantColor(0.33) },
  { label: "Élevé",    t: 0.66, color: pollutantColor(0.66) },
  { label: "Critique", t: 1,    color: pollutantColor(1) },
];

export default function MapChart({ records, pollutant = "pm2_5" }: Props) {
  const [isClient, setIsClient] = useState(false);
  const [LeafletReady, setLeafletReady] = useState(false);

  /* Chargement dynamique de Leaflet (client uniquement) */
  useEffect(() => {
    setIsClient(true);
    import("leaflet").then((leaflet) => {
      L = leaflet.default;
      /* Correction de l'icône par défaut (nécessaire avec Webpack / Next.js) */
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
        iconUrl:       "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
        shadowUrl:     "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
      });
      import("react-leaflet").then((rl) => {
        MapContainer = rl.MapContainer;
        TileLayer    = rl.TileLayer;
        Marker       = rl.Marker;
        Popup        = rl.Popup;
        setLeafletReady(true);
      });
    });
    /* CSS Leaflet */
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement("link");
      link.rel  = "stylesheet";
      link.href = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css";
      document.head.appendChild(link);
    }
  }, []);

  const meta = POLLUTANT_META[pollutant] ?? { label: String(pollutant), unit: "", color: COLORS.teal };

  const filtered = records.filter(
    (r) => r.lat && r.lon && !isNaN(r[pollutant] as number)
  ).slice(-120);

  const vals   = filtered.map((r) => r[pollutant] as number);
  const minVal = vals.length ? Math.min(...vals) : 0;
  const maxVal = vals.length ? Math.max(...vals) : 1;
  const norm   = (v: number) => maxVal > minVal ? (v - minVal) / (maxVal - minVal) : 0.5;

  /* ── Squelette pré-hydratation ── */
  if (!isClient || !LeafletReady) {
    return (
      <div style={{
        height: 400, borderRadius: 12,
        border: "1px solid var(--border)",
        background: "var(--surface2)",
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 12,
        gap: 10,
      }}>
        <div className="live-dot" />
        Chargement de la carte…
      </div>
    );
  }

  return (
    <div style={{
      height: 440, borderRadius: 12, overflow: "hidden",
      border: "1px solid var(--border)",
      position: "relative",
      boxShadow: "var(--shadow-sm)",
    }}>
      <MapContainer
        center={[COTONOU_LAT, COTONOU_LON]}
        zoom={12}
        style={{ height: "100%", width: "100%", zIndex: 0 }}
        scrollWheelZoom={false}
      >
        {/* Tuile adaptée au thème : carto légère */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org">OpenStreetMap</a> &copy; <a href="https://carto.com">CARTO</a>'
          maxZoom={19}
        />

        {filtered.map((rec, i) => {
          const val  = rec[pollutant] as number;
          const t    = norm(val);
          const lat  = typeof rec.lat === "number" ? rec.lat : parseFloat(rec.lat as any);
          const lon  = typeof rec.lon === "number" ? rec.lon : parseFloat(rec.lon as any);
          const size = Math.round(16 + t * 22);
          const col  = pollutantColor(t);

          return (
            <Marker key={i} position={[lat, lon]} icon={createMarker(col, size)}>
              <Popup>
                <div style={{
                  padding: "10px 12px", minWidth: 180,
                  fontFamily: "Outfit, sans-serif", fontSize: 12,
                  lineHeight: 1.6,
                }}>
                  <div style={{
                    fontFamily: "Syne, sans-serif", fontWeight: 700,
                    fontSize: 13, marginBottom: 6,
                    color: col,
                  }}>
                    {meta.label}
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 6, color: col }}>
                    {val.toFixed(1)}
                    <span style={{ fontSize: 11, fontWeight: 400, color: "#888", marginLeft: 4 }}>
                      {meta.unit}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: "#888" }}>📅 {rec.date}</div>
                  <div style={{ fontSize: 11, color: "#888", marginTop: 3 }}>
                    📍 {lat.toFixed(4)}°, {lon.toFixed(4)}°
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* ── Légende ── */}
      <div style={{
        position: "absolute", bottom: 16, left: 12,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 10, padding: "10px 14px",
        fontFamily: "JetBrains Mono, monospace",
        fontSize: 10.5, zIndex: 1000,
        boxShadow: "var(--shadow-md)",
        backdropFilter: "blur(6px)",
      }}>
        <div style={{
          fontFamily: "Syne, sans-serif", fontWeight: 700,
          fontSize: 11, color: "var(--text)",
          marginBottom: 8,
        }}>
          {meta.label}
        </div>

        {/* Gradient bar */}
        <div style={{
          width: 120, height: 8, borderRadius: 4,
          background: "linear-gradient(to right, #00C49A, #F59E0B, #F97316, #EF4444)",
          marginBottom: 6,
        }} />

        <div style={{ display: "flex", justifyContent: "space-between", width: 120, color: "var(--muted)" }}>
          <span>{minVal.toFixed(0)}</span>
          <span>{((minVal + maxVal) / 2).toFixed(0)}</span>
          <span>{maxVal.toFixed(0)} {meta.unit}</span>
        </div>

        {/* Taille des marqueurs */}
        <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 8, color: "var(--muted)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--muted)", opacity: 0.6 }} />
            <span>Faible</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{ width: 18, height: 18, borderRadius: "50%", background: "var(--muted)" }} />
            <span>Élevé</span>
          </div>
        </div>
      </div>

      {/* Compteur de points */}
      <div style={{
        position: "absolute", top: 12, right: 12,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8, padding: "5px 10px",
        fontSize: 10.5, color: "var(--muted)",
        fontFamily: "JetBrains Mono, monospace",
        zIndex: 1000,
      }}>
        {filtered.length} points
      </div>
    </div>
  );
}