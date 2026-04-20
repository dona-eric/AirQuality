"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLLUTANT_META, OMS_THRESHOLDS } from "@/lib/constants";

interface Props {
  records: AirRecord[];
  pollutant: string;
}

function buildHistogram(vals: number[], bins = 40) {
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const step = (max - min) / bins;
  const counts = Array(bins).fill(0);
  for (const v of vals) {
    const idx = Math.min(Math.floor((v - min) / step), bins - 1);
    counts[idx]++;
  }
  return counts.map((count, i) => ({
    bin: +(min + i * step).toFixed(2),
    count,
  }));
}

export default function DistributionChart({ records, pollutant }: Props) {
  const meta = POLLUTANT_META[pollutant];
  const vals = records.map((r) => r[pollutant] as number).filter((v) => v != null && !isNaN(v));
  const hist = buildHistogram(vals);
  const oms = OMS_THRESHOLDS[pollutant];

  // Stats
  const sorted = [...vals].sort((a, b) => a - b);
  const p50 = sorted[Math.floor(sorted.length * 0.5)];
  const p95 = sorted[Math.floor(sorted.length * 0.95)];
  const mean = vals.reduce((a, b) => a + b, 0) / vals.length;

  return (
    <div>
      <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
        {[["Moyenne", mean], ["Médiane (P50)", p50], ["P95", p95]].map(([lbl, v]) => (
          <div key={String(lbl)} style={{ background: "var(--surface2,#111826)", borderRadius: 8, padding: "8px 14px" }}>
            <div style={{ fontSize: 10, color: COLORS.muted, fontFamily: "JetBrains Mono, monospace" }}>{lbl}</div>
            <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Syne, sans-serif", color: meta?.color ?? COLORS.teal }}>
              {(v as number).toFixed(2)}
            </div>
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={hist} margin={{ top: 4, right: 8, left: -10, bottom: 0 }} barSize={6}>
          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
          <XAxis dataKey="bin" tick={{ fontSize: 9, fill: COLORS.muted, fontFamily: "JetBrains Mono" }}
            tickFormatter={(v) => v.toFixed(1)} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 9, fill: COLORS.muted }} />
          <Tooltip
            formatter={(v: any) => [v, "Fréquence"]}
            labelFormatter={(l) => `≈ ${Number(l).toFixed(2)} ${meta?.unit}`}
            contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 8, fontSize: 11, fontFamily: "JetBrains Mono" }}
          />
          {oms && (
            <ReferenceLine x={oms} stroke={COLORS.danger} strokeDasharray="4 4"
              label={{ value: `OMS ${oms}`, fill: COLORS.danger, fontSize: 9, position: "insideTopRight" }} />
          )}
          <Bar dataKey="count" fill={meta?.color ?? COLORS.teal} opacity={0.8} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}