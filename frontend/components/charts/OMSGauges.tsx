"use client";
import { COLORS } from "@/lib/constants";

interface GaugeProps { label: string; value: number; threshold: number; unit?: string }

function Gauge({ label, value, threshold, unit = "μg/m³" }: GaugeProps) {
  const pct   = Math.min(value / (threshold * 2), 1);
  const angle = -135 + pct * 270;                  // arc: -135° → +135°
  const r     = 48;
  const cx    = 64;
  const cy    = 64;

  // Polar to Cartesian
  const toXY = (deg: number) => ({
    x: cx + r * Math.cos((deg * Math.PI) / 180),
    y: cy + r * Math.sin((deg * Math.PI) / 180),
  });

  const arcPath = (startDeg: number, endDeg: number) => {
    const s = toXY(startDeg);
    const e = toXY(endDeg);
    const large = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
  };

  const needle = toXY(angle);
  const over   = value > threshold;
  const color  = over ? COLORS.danger : value > threshold * 0.75 ? COLORS.amber : COLORS.teal;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width={128} height={84} viewBox="0 0 128 84">
        {/* Background arc */}
        <path d={arcPath(-135, 135)} fill="none" stroke="#1A2438" strokeWidth={10} strokeLinecap="round" />
        {/* Zone arcs */}
        <path d={arcPath(-135, -135 + 270 * 0.4)} fill="none" stroke={COLORS.teal}   strokeWidth={10} strokeLinecap="butt" opacity={0.5} />
        <path d={arcPath(-135 + 270 * 0.4, -135 + 270 * 0.7)} fill="none" stroke={COLORS.amber}  strokeWidth={10} strokeLinecap="butt" opacity={0.5} />
        <path d={arcPath(-135 + 270 * 0.7, 135)}  fill="none" stroke={COLORS.danger} strokeWidth={10} strokeLinecap="butt" opacity={0.5} />
        {/* Value arc */}
        <path d={arcPath(-135, angle)} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" />
        {/* Needle */}
        <line x1={cx} y1={cy} x2={needle.x} y2={needle.y} stroke={color} strokeWidth={2} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={4} fill={color} />
        {/* Value */}
        <text x={cx} y={cy + 18} textAnchor="middle" fontSize={13} fontWeight={800}
          fill={color} fontFamily="Syne, sans-serif">{value.toFixed(1)}</text>
      </svg>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: COLORS.muted, textAlign: "center" }}>
        {label}
      </div>
      <div style={{ fontSize: 10, color: over ? COLORS.danger : COLORS.teal, fontFamily: "JetBrains Mono, monospace", marginTop: 2 }}>
        seuil {threshold} {unit}
        {over && <span style={{ marginLeft: 4, fontWeight: 700 }}>▲ dépassé</span>}
      </div>
    </div>
  );
}

interface Props {
  pm25: number; pm10: number; o3: number; no2: number;
}

export default function OMSGauges({ pm25, pm10, o3, no2 }: Props) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16 }}>
      <Gauge label="PM2.5"   value={pm25} threshold={12}  />
      <Gauge label="PM10"    value={pm10} threshold={40}  />
      <Gauge label="Ozone O₃" value={o3}  threshold={100} />
      <Gauge label="NO₂"     value={no2}  threshold={10}  />
    </div>
  );
}