"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import type { HourlyRow } from "@/lib/types";
import { COLORS } from "@/lib/constants";

interface Props { data: HourlyRow[] }

const PANELS = [
  { key: "pm2_5",            label: "PM2.5",  unit: "μg/m³", color: COLORS.coral  },
  { key: "pm10",             label: "PM10",   unit: "μg/m³", color: COLORS.amber  },
  { key: "ozone",            label: "O₃",     unit: "μg/m³", color: COLORS.teal   },
  { key: "nitrogen_dioxide", label: "NO₂",    unit: "μg/m³", color: COLORS.indigo },
  { key: "sulphur_dioxide",  label: "SO₂",    unit: "μg/m³", color: COLORS.muted  },
  { key: "carbon_monoxide",  label: "CO",     unit: "μg/m³", color: COLORS.violet },
] as const;

const tooltipStyle = {
  background:   "var(--surface2)",
  border:       "1px solid var(--border)",
  borderRadius: 8,
  fontSize:     11,
  fontFamily:   "JetBrains Mono, monospace",
  color:        "var(--text)",
  boxShadow:    "var(--shadow-md)",
  padding:      "6px 10px",
};

export default function HourlyChart({ data }: Props) {
  return (
    /*
     * FIX : minWidth: 0 sur le conteneur de grille ET sur chaque enfant.
     * Sans ça, les cellules CSS Grid n'ont pas de largeur mesurable →
     * ResponsiveContainer reçoit width = -1 et lance l'avertissement.
     */
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 14,
      minWidth: 0,        /* ← indispensable sur la grille parente */
    }}>
      {PANELS.map(({ key, label, unit, color }) => (
        <div
          key={key}
          style={{
            background: "var(--surface2)",
            border: "1px solid var(--border)",
            borderRadius: 10,
            padding: "12px 14px",
            transition: "box-shadow 0.2s ease",
            minWidth: 0,  /* ← indispensable sur chaque enfant de grille */
            overflow: "hidden",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "var(--shadow-md)")}
          onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
        >
          {/* En-tête */}
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
            <span style={{
              display: "inline-block", width: 8, height: 8,
              borderRadius: "50%", background: color, flexShrink: 0,
            }} />
            <span style={{
              fontSize: 11, color: "var(--text)",
              fontFamily: "JetBrains Mono, monospace",
              fontWeight: 600, letterSpacing: "0.03em",
            }}>
              {label}
            </span>
            <span style={{ fontSize: 9, color: "var(--muted)", fontFamily: "JetBrains Mono, monospace" }}>
              {unit}
            </span>
          </div>

          {/*
           * Wrapper hauteur FIXE : ResponsiveContainer mesure ce div,
           * pas son parent. height="100%" est alors fiable.
           */}
          <div style={{ width: "100%", height: 100 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 2, right: 4, left: -24, bottom: 0 }}>
                <defs>
                  <linearGradient id={`hg-${key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={color} stopOpacity={0.01} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="hour"
                  tickFormatter={(h) => h % 6 === 0 ? `${h}h` : ""}
                  tick={{ fontSize: 8, fill: "var(--muted)" }}
                  tickLine={false} axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 8, fill: "var(--muted)" }}
                  tickLine={false} axisLine={false} width={32}
                />
                <Tooltip
                  formatter={(v: any) => [`${Number(v).toFixed(2)} ${unit}`, label]}
                  contentStyle={tooltipStyle}
                  itemStyle={{ color }}
                  cursor={{ stroke: color, strokeWidth: 1, strokeOpacity: 0.4 }}
                />
                <Area
                  type="monotone"
                  dataKey={key as string}
                  stroke={color} strokeWidth={2}
                  fill={`url(#hg-${key})`}
                  dot={false}
                  activeDot={{ r: 4, fill: color, stroke: "var(--surface)", strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      ))}
    </div>
  );
}