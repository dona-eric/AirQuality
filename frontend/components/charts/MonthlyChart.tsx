"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { DailyRow } from "@/lib/types";
import { COLORS } from "@/lib/constants";

interface Props { daily: DailyRow[] }

const MONTH_LABELS: Record<string, string> = {
  "2025-09": "Sept 25", "2025-10": "Oct 25", "2025-11": "Nov 25",
  "2025-12": "Déc 25",  "2026-01": "Jan 26",  "2026-02": "Fév 26",
  "2026-03": "Mar 26",  "2026-04": "Avr 26",
};

export default function MonthlyChart({ daily }: Props) {
  // Group by month
  const byMonth = new Map<string, DailyRow[]>();
  for (const r of daily) {
    const m = r.date.slice(0, 7);
    if (!byMonth.has(m)) byMonth.set(m, []);
    byMonth.get(m)!.push(r);
  }
  const data = Array.from(byMonth.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([m, rows]) => {
      const avg = (col: keyof DailyRow) =>
        +(rows.reduce((s, r) => s + (r[col] as number || 0), 0) / rows.length).toFixed(2);
      return {
        month: MONTH_LABELS[m] ?? m,
        "PM2.5": avg("pm2_5"),
        "PM10":  avg("pm10"),
        "O₃":   avg("ozone"),
        "NO₂":  avg("nitrogen_dioxide"),
        "SO₂":  avg("sulphur_dioxide"),
      };
    });

  const BARS = [
    { key: "PM2.5", color: COLORS.coral },
    { key: "PM10",  color: COLORS.amber },
    { key: "O₃",    color: COLORS.teal },
    { key: "NO₂",   color: COLORS.indigo },
    { key: "SO₂",   color: COLORS.muted },
  ];

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -10, bottom: 0 }} barSize={10}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
        <XAxis dataKey="month" tick={{ fontSize: 10, fill: COLORS.muted, fontFamily: "JetBrains Mono" }} />
        <YAxis tick={{ fontSize: 10, fill: COLORS.muted }} />
        <Tooltip
          contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 8, fontSize: 11, fontFamily: "JetBrains Mono" }}
          labelStyle={{ color: COLORS.text }}
        />
        <Legend iconSize={8} wrapperStyle={{ fontSize: 11, color: COLORS.muted }} />
        {BARS.map(({ key, color }) => (
          <Bar key={key} dataKey={key} stackId="a" fill={color} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}