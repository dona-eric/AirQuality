"use client";
import { useState } from "react";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLLUTANT_META } from "@/lib/constants";
import { getAqiLabel } from "@/lib/api";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard from "@/components/ui/ChartCard";
import DistributionChart from "@/components/charts/DistributionChart";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";

interface Props { records: AirRecord[] }

const AQI_COLORS_MAP: Record<string, string> = {
  Bon: "#0D9488", Moyen: "#F59E0B", Mauvais: "#EF4444",
};

function ScatterByAQI({ records, xKey }: { records: AirRecord[]; xKey: string }) {
  const meta = POLLUTANT_META[xKey];
  const sample = records
    .filter((r) => !isNaN(r[xKey] as number) && !isNaN(r.pm2_5 as number))
    .slice(0, 1500);

  const grouped: Record<string, { x: number; y: number }[]> = { Bon: [], Moyen: [], Mauvais: [] };
  for (const r of sample) {
    const lbl = getAqiLabel(r.pm2_5 as number);
    grouped[lbl].push({ x: +(r[xKey] as number).toFixed(2), y: +(r.pm2_5 as number).toFixed(2) });
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis dataKey="x" name={meta?.label ?? xKey} type="number" tick={{ fontSize: 9, fill: COLORS.muted }} label={{ value: meta?.label ?? xKey, position: "insideBottom", offset: -4, fontSize: 10, fill: COLORS.muted }} />
        <YAxis dataKey="y" name="PM2.5" type="number" tick={{ fontSize: 9, fill: COLORS.muted }} label={{ value: "PM2.5", angle: -90, position: "insideLeft", fontSize: 10, fill: COLORS.muted }} />
        <Tooltip
          formatter={(v: number, n: string) => [v.toFixed(2), n]}
          contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 8, fontSize: 11, fontFamily: "JetBrains Mono" }}
        />
        {Object.entries(grouped).map(([lbl, pts]) => (
          <Scatter key={lbl} name={lbl} data={pts} fill={AQI_COLORS_MAP[lbl]} opacity={0.55} />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export default function Distributions({ records }: Props) {
  const pollKeys = Object.keys(POLLUTANT_META);
  const [distPoll, setDistPoll] = useState("pm2_5");
  const [relPoll, setRelPoll]   = useState("pm10");

  const Selector = ({ value, onChange, exclude }: { value: string; onChange: (v: string) => void; exclude?: string }) => (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
      {pollKeys.filter((k) => k !== exclude).map((k) => {
        const m = POLLUTANT_META[k];
        const active = value === k;
        return (
          <button key={k} onClick={() => onChange(k)}
            style={{
              padding: "3px 10px", borderRadius: 14,
              border: `1px solid ${active ? m.color : COLORS.border}`,
              background: active ? `${m.color}18` : "transparent",
              color: active ? m.color : COLORS.muted,
              fontSize: 11, fontFamily: "JetBrains Mono, monospace", cursor: "pointer",
            }}>
            {m.label}
          </button>
        );
      })}
    </div>
  );

  return (
    <div>
      <SectionTitle>📊 Distribution des polluants</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <ChartCard title="Distribution & histogramme" delay={0}>
          <Selector value={distPoll} onChange={setDistPoll} />
          <DistributionChart records={records} pollutant={distPoll} />
        </ChartCard>

        <ChartCard title="Relation PM2.5 vs polluant" delay={80}>
          <Selector value={relPoll} onChange={setRelPoll} exclude="pm2_5" />
          <ScatterByAQI records={records} xKey={relPoll} />
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            {Object.entries(AQI_COLORS_MAP).map(([lbl, c]) => (
              <div key={lbl} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: c, display: "inline-block" }} />
                <span style={{ fontSize: 10, color: COLORS.muted, fontFamily: "JetBrains Mono, monospace" }}>{lbl}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </div>
  );
}