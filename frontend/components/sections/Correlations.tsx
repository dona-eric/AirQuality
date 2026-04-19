"use client";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLL_COLS } from "@/lib/constants";
import { computeCorrelation } from "@/lib/api";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard from "@/components/ui/ChartCard";
import CorrelationHeatmap from "@/components/charts/CorrelationHeatmap";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Line, ResponsiveContainer, ComposedChart,
} from "recharts";

interface Props { records: AirRecord[] }

function PMScatter({ records }: { records: AirRecord[] }) {
  const sample = records
    .filter((r) => !isNaN(r.pm2_5 as number) && !isNaN(r.pm10 as number))
    .slice(0, 1200)
    .map((r) => ({ x: +(r.pm10 as number).toFixed(2), y: +(r.pm2_5 as number).toFixed(2) }));

  // Linear regression
  const n  = sample.length;
  const sx = sample.reduce((s, p) => s + p.x, 0);
  const sy = sample.reduce((s, p) => s + p.y, 0);
  const sxx= sample.reduce((s, p) => s + p.x ** 2, 0);
  const sxy= sample.reduce((s, p) => s + p.x * p.y, 0);
  const b  = (n * sxy - sx * sy) / (n * sxx - sx ** 2);
  const a  = (sy - b * sx) / n;
  const xMin = Math.min(...sample.map((p) => p.x));
  const xMax = Math.max(...sample.map((p) => p.x));
  const regLine = [{ x: xMin, reg: +(a + b * xMin).toFixed(2) }, { x: xMax, reg: +(a + b * xMax).toFixed(2) }];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis dataKey="x" type="number" name="PM10" tick={{ fontSize: 9, fill: COLORS.muted }}
          label={{ value: "PM10 μg/m³", position: "insideBottom", offset: -4, fontSize: 10, fill: COLORS.muted }} />
        <YAxis dataKey="y" type="number" name="PM2.5" tick={{ fontSize: 9, fill: COLORS.muted }}
          label={{ value: "PM2.5", angle: -90, position: "insideLeft", fontSize: 10, fill: COLORS.muted }} />
        <Tooltip
          formatter={(v: number, n: string) => [v.toFixed(2), n]}
          contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 8, fontSize: 11, fontFamily: "JetBrains Mono" }}
        />
        <Scatter data={sample} fill={COLORS.amber} opacity={0.4} />
        <Line data={regLine} dataKey="reg" dot={false} stroke={COLORS.danger} strokeWidth={2} strokeDasharray="5 3" legendType="none" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export default function Correlations({ records }: Props) {
  const cols = POLL_COLS.filter((c) => records.some((r) => !isNaN(r[c] as number)));
  const matrix = computeCorrelation(records, cols);

  return (
    <div>
      <SectionTitle>🔗 Relations & corrélations</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <ChartCard title="Densité PM2.5 vs PM10" caption="Régression linéaire + nuage de points" delay={0}>
          <PMScatter records={records} />
        </ChartCard>
        <ChartCard title="Matrice de corrélation des polluants" caption="Coefficient de Pearson r ∈ [−1, 1]" delay={80}>
          <CorrelationHeatmap matrix={matrix} labels={cols.map((c) => {
            const s: Record<string, string> = { pm2_5:"PM2.5", pm10:"PM10", carbon_monoxide:"CO", carbon_dioxide:"CO₂", sulphur_dioxide:"SO₂", ozone:"O₃", nitrogen_dioxide:"NO₂", methane:"CH₄", european_aqi:"AQI" };
            return s[c] ?? c;
          })} />
        </ChartCard>
      </div>
    </div>
  );
}