"use client";
import { useState } from "react";
import type { AirRecord, DailyRow } from "@/lib/types";
import { COLORS, POLLUTANT_META } from "@/lib/constants";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard from "@/components/ui/ChartCard";
import TimeSeriesChart from "@/components/charts/TimeSeriesChart";

interface Props { records: AirRecord[]; daily: DailyRow[] }

// Simple IsolationForest-like: flag points beyond 2σ as anomalies
function detectAnomalies(records: AirRecord[]): Set<string> {
  const vals = records.map((r) => r.pm2_5 as number).filter((v) => !isNaN(v));
  const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
  const std  = Math.sqrt(vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length);
  const anomalyDates = new Set<string>();
  for (const r of records) {
    if (Math.abs((r.pm2_5 as number) - mean) > 2 * std) {
      anomalyDates.add(r.date.slice(0, 10));
    }
  }
  return anomalyDates;
}

// Day-of-week heatmap (pure SVG)
function DayHourHeatmap({ records }: { records: AirRecord[] }) {
  const DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
  const grid: number[][] = Array.from({ length: 7 }, () => Array(24).fill(0));
  const counts: number[][] = Array.from({ length: 7 }, () => Array(24).fill(0));
  for (const r of records) {
    const d = new Date(r.date);
    const dow = (d.getUTCDay() + 6) % 7; // Mon=0
    const h   = d.getUTCHours();
    grid[dow][h]   += (r.pm2_5 as number) || 0;
    counts[dow][h] += 1;
  }
  const avgs = grid.map((row, i) => row.map((v, j) => counts[i][j] ? v / counts[i][j] : 0));
  const allVals = avgs.flat();
  const minV = Math.min(...allVals);
  const maxV = Math.max(...allVals);
  const norm = (v: number) => maxV > minV ? (v - minV) / (maxV - minV) : 0;

  const CW = 22; const CH = 22;
  const PL = 36; const PT = 20;
  const W  = PL + 24 * CW + 10;
  const H  = PT + 7 * CH + 10;

  const toColor = (v: number) => {
    const t = norm(v);
    const r = Math.round(14  + t * (239 - 14));
    const g = Math.round(20  + t * (68  - 20));
    const b = Math.round(36  + t * (68  - 36));
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <svg width={W} height={H}>
        {Array.from({ length: 24 }, (_, h) => (
          h % 3 === 0 && (
            <text key={h} x={PL + h * CW + CW / 2} y={14}
              textAnchor="middle" fontSize={8} fill={COLORS.muted} fontFamily="JetBrains Mono, monospace">
              {h}h
            </text>
          )
        ))}
        {DAYS.map((day, i) => (
          <text key={day} x={PL - 4} y={PT + i * CH + CH / 2 + 4}
            textAnchor="end" fontSize={9} fill={COLORS.muted} fontFamily="JetBrains Mono, monospace">
            {day}
          </text>
        ))}
        {avgs.map((row, i) =>
          row.map((v, j) => (
            <rect key={`${i}-${j}`}
              x={PL + j * CW + 1} y={PT + i * CH + 1}
              width={CW - 2} height={CH - 2}
              fill={toColor(v)} rx={2} opacity={0.9}>
              <title>{`${DAYS[i]} ${j}h → PM2.5: ${v.toFixed(1)} μg/m³`}</title>
            </rect>
          ))
        )}
      </svg>
    </div>
  );
}

export default function TimeSeries({ records, daily }: Props) {
  const pollKeys = Object.keys(POLLUTANT_META);
  const [poll, setPoll] = useState<string>("pm2_5");
  const anomalies = detectAnomalies(records);

  return (
    <div>
      <SectionTitle>📈 Série temporelle + anomalies détectées</SectionTitle>

      {/* Selector */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14, minWidth:0}}>
        {pollKeys.map((k) => {
          const m = POLLUTANT_META[k];
          const active = poll === k;
          return (
            <button key={k} onClick={() => setPoll(k)}
              style={{
                padding: "5px 12px",
                borderRadius: 20,
                border: `1px solid ${active ? m.color : COLORS.border}`,
                background: active ? `${m.color}18` : "transparent",
                color: active ? m.color : COLORS.muted,
                fontSize: 12,
                fontFamily: "JetBrains Mono, monospace",
                cursor: "pointer",
                transition: "all 0.15s",
              }}>
              {m.label}
            </button>
          );
        })}
      </div>

      <ChartCard delay={0}>
        <TimeSeriesChart
          daily={daily}
          anomalyDates={anomalies}
          pollutant={poll as keyof typeof POLLUTANT_META}
        />
      </ChartCard>

      <SectionTitle>🕐 Analyse temporelle avancée</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <ChartCard title="Cycle pollution : heure × jour de la semaine" caption="Moyenne PM2.5 μg/m³" delay={0}>
          <DayHourHeatmap records={records} />
        </ChartCard>
        <ChartCard title="Statistiques mensuelles PM2.5" delay={80}>
          <MonthlyBoxStats daily={daily} />
        </ChartCard>
      </div>
    </div>
  );
}

// Compact monthly stats table instead of boxplot
function MonthlyBoxStats({ daily }: { daily: DailyRow[] }) {
  const byMonth = new Map<string, number[]>();
  for (const r of daily) {
    const m = r.date.slice(0, 7);
    if (!byMonth.has(m)) byMonth.set(m, []);
    byMonth.get(m)!.push(r.pm2_5);
  }
  const months = Array.from(byMonth.entries()).sort(([a], [b]) => a.localeCompare(b)).map(([m, vals]) => {
    const sorted = [...vals].sort((a, b) => a - b);
    return {
      month: m.slice(2),
      min:   sorted[0]?.toFixed(1) ?? "—",
      p25:   sorted[Math.floor(sorted.length * 0.25)]?.toFixed(1) ?? "—",
      med:   sorted[Math.floor(sorted.length * 0.5)]?.toFixed(1) ?? "—",
      p75:   sorted[Math.floor(sorted.length * 0.75)]?.toFixed(1) ?? "—",
      max:   sorted[sorted.length - 1]?.toFixed(1) ?? "—",
    };
  });

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, fontFamily: "JetBrains Mono, monospace" }}>
        <thead>
          <tr>
            {["Mois", "Min", "P25", "Médiane", "P75", "Max"].map((h) => (
              <th key={h} style={{ padding: "6px 10px", textAlign: "left", color: COLORS.muted, fontWeight: 600, borderBottom: `1px solid ${COLORS.border}`, fontSize: 10 }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {months.map((row) => (
            <tr key={row.month} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {[row.month, row.min, row.p25, row.med, row.p75, row.max].map((v, i) => (
                <td key={i} style={{ padding: "7px 10px", color: i === 3 ? COLORS.coral : "var(--text)" }}>
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}