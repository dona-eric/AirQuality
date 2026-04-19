"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import type { HourlyRow } from "@/lib/types";
import { COLORS } from "@/lib/constants";

interface Props { data: HourlyRow[] }

const PANELS = [
  { key: "pm2_5",           label: "PM2.5 μg/m³",  color: COLORS.coral  },
  { key: "pm10",            label: "PM10 μg/m³",   color: COLORS.amber  },
  { key: "ozone",           label: "O₃ μg/m³",     color: COLORS.teal   },
  { key: "nitrogen_dioxide",label: "NO₂ μg/m³",    color: COLORS.indigo },
  { key: "sulphur_dioxide", label: "SO₂ μg/m³",    color: COLORS.muted  },
  { key: "carbon_dioxide",  label: "CO₂ μg/m³",    color: COLORS.violet },
] as const;

export default function HourlyChart({ data }: Props) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }}>
      {PANELS.map(({ key, label, color }) => (
        <div key={key}>
          <div style={{ fontSize: 11, color: COLORS.muted, fontFamily: "JetBrains Mono, monospace", marginBottom: 6 }}>
            {label}
          </div>
          <ResponsiveContainer width="100%" height={110}>
            <AreaChart data={data} margin={{ top: 0, right: 6, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id={`g-${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
              <XAxis dataKey="hour" tickFormatter={(h) => h % 6 === 0 ? `${h}h` : ""} tick={{ fontSize: 9, fill: COLORS.muted }} />
              <YAxis tick={{ fontSize: 9, fill: COLORS.muted }} />
              <Tooltip
                formatter={(v: number) => [v.toFixed(2), label]}
                contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 6, fontSize: 11, fontFamily: "JetBrains Mono" }}
              />
              <Area type="monotone" dataKey={key as string} stroke={color} strokeWidth={2} fill={`url(#g-${key})`} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  );
}