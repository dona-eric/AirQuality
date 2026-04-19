"use client";
import { useEffect } from "react";
import type { AirRecord, PredictionResponse, HistoryResponse } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard from "@/components/ui/ChartCard";
import AIInsightsPanel from "@/components/IAInsights";
import { useAIInsights } from "@/lib/useiainsights";

interface Props {
  records: AirRecord[];
  prediction: PredictionResponse | null;
  history: HistoryResponse | null;
}


export default function MLInsights({ records, prediction, history }: Props) {
  const { data, loading, streaming, rawText, error, fetch: fetchInsights } = useAIInsights();

  useEffect(() => {
    if (records.length > 0) {
      fetchInsights(records, prediction, history);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const vals = (col: string) =>
    records.map((r) => r[col] as number).filter((v) => v != null && !isNaN(v));
  const mean = (a: number[]) =>
    a.length ? +(a.reduce((s, v) => s + v, 0) / a.length).toFixed(2) : 0;
  const q95 = (a: number[]) => {
    const s = [...a].sort((x, y) => x - y);
    return +(s[Math.floor(s.length * 0.95)] ?? 0).toFixed(2);
  };
  const pct = (a: number[], thr: number) =>
    +((a.filter((v) => v > thr).length / (a.length || 1)) * 100).toFixed(1);

  const pm25 = vals("pm2_5");
  const pm10 = vals("pm10");
  const o3   = vals("ozone");
  const no2  = vals("nitrogen_dioxide");
  const aqi  = vals("european_aqi");

  const tableRows = [
    { label: "PM2.5 Moyen",     value: `${mean(pm25)} μg/m³`, oms: "12 μg/m³",  ok: mean(pm25) <= 12 },
    { label: "PM10 Moyen",      value: `${mean(pm10)} μg/m³`, oms: "40 μg/m³",  ok: mean(pm10) <= 40 },
    { label: "Ozone Moyen",     value: `${mean(o3)} μg/m³`,   oms: "100 μg/m³", ok: mean(o3) <= 100 },
    { label: "NO₂ Moyen",       value: `${mean(no2)} μg/m³`,  oms: "10 μg/m³",  ok: mean(no2) <= 10 },
    { label: "AQI Moyen",       value: String(mean(aqi)),      oms: "75",         ok: mean(aqi) <= 50 },
    { label: "PM2.5 P95",       value: `${q95(pm25)} μg/m³`,  oms: "—",          ok: true },
    { label: "Heures AQI > 60", value: `${pct(aqi, 60)}%`,    oms: "0%",         ok: pct(aqi, 60) === 0 },
    { label: "Total mesures",   value: records.length.toLocaleString("fr"), oms: "—", ok: true },
  ];

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "0 0 18px" }}>
        <SectionTitle>🤖 Analyse & Recommandations IA</SectionTitle>
        {!loading && !streaming && (
          <button
            onClick={() => fetchInsights(records, prediction, history)}
            style={{
              background: `${COLORS.teal}12`, border: `1px solid ${COLORS.teal}`,
              borderRadius: 8, color: COLORS.teal, padding: "6px 14px",
              fontSize: 12, fontFamily: "JetBrains Mono, monospace", cursor: "pointer",
              transition: "all 0.15s", whiteSpace: "nowrap",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = COLORS.teal; e.currentTarget.style.color = "#080C14"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = `${COLORS.teal}12`; e.currentTarget.style.color = COLORS.teal; }}
          >
            ↺ Rafraîchir l'analyse
          </button>
        )}
      </div>

      <AIInsightsPanel
        data={data}
        loading={loading}
        streaming={streaming}
        rawText={rawText}
        error={error}
        onRefresh={() => fetchInsights(records, prediction, history)}
      />

      <SectionTitle>📋 Statistiques résumées vs seuils OMS</SectionTitle>
      <ChartCard delay={0}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, fontFamily: "JetBrains Mono, monospace" }}>
            <thead>
              <tr>
                {["Indicateur", "Valeur", "Seuil OMS", "Statut"].map((h) => (
                  <th key={h} style={{ padding: "8px 14px", textAlign: "left", color: COLORS.muted, fontWeight: 600, borderBottom: `1px solid ${COLORS.border}`, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row) => (
                <tr key={row.label} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: "10px 14px", color: "var(--text)" }}>{row.label}</td>
                  <td style={{ padding: "10px 14px", color: COLORS.teal, fontWeight: 600 }}>{row.value}</td>
                  <td style={{ padding: "10px 14px", color: COLORS.muted }}>{row.oms}</td>
                  <td style={{ padding: "10px 14px" }}>
                    {row.oms === "—" ? (
                      <span style={{ color: COLORS.muted, fontSize: 10 }}>—</span>
                    ) : (
                      <span style={{
                        fontSize: 10, padding: "2px 8px", borderRadius: 10, fontWeight: 600,
                        background: row.ok ? "rgba(13,148,136,0.12)" : "rgba(239,68,68,0.12)",
                        color: row.ok ? COLORS.teal : COLORS.danger,
                      }}>
                        {row.ok ? "✓ OK" : "✗ Dépassé"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  );
}