"use client";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLL_COLS } from "@/lib/constants";
import { computeCorrelation } from "@/lib/api";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard    from "@/components/ui/ChartCard";
import CorrelationHeatmap from "@/components/charts/CorrelationHeatmap";
import {
  ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Line, ResponsiveContainer, ComposedChart,
} from "recharts";

interface Props { records: AirRecord[] }

/* Tooltip commun adaptatif */
const tooltipStyle = {
  background:   "var(--surface2)",
  border:       "1px solid var(--border)",
  borderRadius: 8,
  fontSize:     11,
  fontFamily:   "JetBrains Mono, monospace",
  color:        "var(--text)",
  boxShadow:    "var(--shadow-md)",
};

/* ── Scatter PM2.5 vs PM10 avec droite de régression ── */
function PMScatter({ records }: { records: AirRecord[] }) {
  const sample = records
    .filter((r) => !isNaN(r.pm2_5 as number) && !isNaN(r.pm10 as number))
    .slice(0, 1200)
    .map((r) => ({
      x: +(r.pm10  as number).toFixed(2),
      y: +(r.pm2_5 as number).toFixed(2),
    }));

  /* Régression linéaire (moindres carrés) */
  const n   = sample.length || 1;
  const sx  = sample.reduce((s, p) => s + p.x, 0);
  const sy  = sample.reduce((s, p) => s + p.y, 0);
  const sxx = sample.reduce((s, p) => s + p.x ** 2, 0);
  const sxy = sample.reduce((s, p) => s + p.x * p.y, 0);
  const b   = (n * sxy - sx * sy) / (n * sxx - sx ** 2 || 1);
  const a   = (sy - b * sx) / n;

  const xs     = sample.map((p) => p.x);
  const xMin   = Math.min(...xs);
  const xMax   = Math.max(...xs);
  const regLine = [
    { x: xMin, reg: +(a + b * xMin).toFixed(2) },
    { x: xMax, reg: +(a + b * xMax).toFixed(2) },
  ];

  /* Coefficient r² */
  const meanY = sy / n;
  const ss_res = sample.reduce((s, p) => s + (p.y - (a + b * p.x)) ** 2, 0);
  const ss_tot = sample.reduce((s, p) => s + (p.y - meanY) ** 2, 0);
  const r2 = ss_tot > 0 ? 1 - ss_res / ss_tot : 0;

  return (
    <div>
      {/* Badge r² */}
      <div style={{
        display: "flex", justifyContent: "flex-end", marginBottom: 8,
      }}>
        <span style={{
          fontSize: 11, fontFamily: "JetBrains Mono, monospace",
          background: `${COLORS.amber}18`,
          border: `1px solid ${COLORS.amber}40`,
          color: COLORS.amber,
          borderRadius: 20, padding: "2px 10px",
        }}>
          r² = {r2.toFixed(3)}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart margin={{ top: 6, right: 10, left: -10, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />

          <XAxis
            dataKey="x" type="number" name="PM10"
            tick={{ fontSize: 9, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
            label={{
              value: "PM10 μg/m³",
              position: "insideBottom", offset: -10,
              fontSize: 10, fill: "var(--muted)",
            }}
          />
          <YAxis
            dataKey="y" type="number" name="PM2.5"
            tick={{ fontSize: 9, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
            label={{
              value: "PM2.5 μg/m³",
              angle: -90, position: "insideLeft",
              fontSize: 10, fill: "var(--muted)",
            }}
          />

          <Tooltip
            formatter={(v: any, n: any) => [`${Number(v).toFixed(2)} μg/m³`, n]}
            contentStyle={tooltipStyle}
            cursor={{ stroke: "var(--border)", strokeWidth: 1 }}
          />

          {/* Nuage de points */}
          <Scatter
            data={sample}
            fill={COLORS.amber}
            opacity={0.35}
            r={3}
          />

          {/* Droite de régression */}
          <Line
            data={regLine}
            dataKey="reg"
            dot={false}
            stroke={COLORS.danger}
            strokeWidth={2}
            strokeDasharray="6 3"
            legendType="none"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

/* Noms courts des colonnes pour la heatmap */
const COL_LABELS: Record<string, string> = {
  pm2_5:             "PM2.5",
  pm10:              "PM10",
  carbon_monoxide:   "CO",
  carbon_dioxide:    "CO₂",
  sulphur_dioxide:   "SO₂",
  ozone:             "O₃",
  nitrogen_dioxide:  "NO₂",
  methane:           "CH₄",
  european_aqi:      "AQI",
};

/* ── Section principale ── */
export default function Correlations({ records }: Props) {
  const cols   = POLL_COLS.filter((c) => records.some((r) => !isNaN(r[c] as number)));
  const matrix = computeCorrelation(records, cols);
  const labels = cols.map((c) => COL_LABELS[c] ?? c);

  return (
    <div>
      <SectionTitle>🔗 Relations & corrélations</SectionTitle>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <ChartCard
          title="Densité PM2.5 vs PM10"
          caption="Nuage de points + régression linéaire (moindres carrés)"
          delay={0}
        >
          <PMScatter records={records} />
        </ChartCard>

        <ChartCard
          title="Matrice de corrélation des polluants"
          caption="Coefficient de Pearson r ∈ [−1 ; 1]"
          delay={80}
        >
          <CorrelationHeatmap matrix={matrix} labels={labels} />
        </ChartCard>
      </div>
    </div>
  );
}