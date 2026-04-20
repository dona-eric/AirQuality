"use client";
import { useEffect } from "react";
import type { AirRecord, PredictionResponse, HistoryResponse } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard    from "@/components/ui/ChartCard";
import AIInsightsPanel from "@/components/IAInsights";
import { useAIInsights } from "@/lib/useiainsights";

interface Props {
  records:    AirRecord[];
  prediction: PredictionResponse | null;
  history:    HistoryResponse | null;
}

export default function MLInsights({ records, prediction, history }: Props) {
  const { data, loading, streaming, rawText, error, fetch: fetchInsights } = useAIInsights();

  useEffect(() => {
    if (records.length > 0) fetchInsights(records, prediction, history);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Helpers stats ── */
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
    { label: "Ozone Moyen",     value: `${mean(o3)} μg/m³`,   oms: "100 μg/m³", ok: mean(o3)   <= 100 },
    { label: "NO₂ Moyen",       value: `${mean(no2)} μg/m³`,  oms: "10 μg/m³",  ok: mean(no2)  <= 10  },
    { label: "AQI Moyen",       value: String(mean(aqi)),      oms: "75",         ok: mean(aqi)  <= 50  },
    { label: "PM2.5 P95",       value: `${q95(pm25)} μg/m³`,  oms: "—",          ok: true },
    { label: "Heures AQI > 60", value: `${pct(aqi, 60)}%`,    oms: "0%",         ok: pct(aqi, 60) === 0 },
    { label: "Total mesures",   value: records.length.toLocaleString("fr"), oms: "—", ok: true },
  ];

  /* ── Styles partagés ── */
  const thStyle: React.CSSProperties = {
    padding: "10px 16px",
    textAlign: "left",
    fontFamily: "JetBrains Mono, monospace",
    fontWeight: 700,              /* était 600 */
    fontSize: 11,                 /* était 10 */
    textTransform: "uppercase",
    letterSpacing: "0.10em",
    color: "var(--text)",         /* plus de contraste que COLORS.muted */
    borderBottom: "2px solid var(--border)",
    whiteSpace: "nowrap",
  };

  const tdBase: React.CSSProperties = {
    padding: "11px 16px",
    fontSize: 13,                 /* était 12 — plus lisible */
    lineHeight: 1.5,
    borderBottom: "1px solid var(--border)",
  };

  return (
    <div>
      {/* ── En-tête section ── */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", margin: "0 0 18px",
      }}>
        <SectionTitle>🤖 Analyse & Recommandations IA</SectionTitle>

        {!loading && !streaming && (
          <button
            onClick={() => fetchInsights(records, prediction, history)}
            style={{
              background: `${COLORS.teal}12`,
              border: `1px solid ${COLORS.teal}`,
              borderRadius: 8, color: COLORS.teal,
              padding: "7px 16px",
              fontSize: 12,
              fontFamily: "JetBrains Mono, monospace",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s",
              whiteSpace: "nowrap",
              letterSpacing: "0.03em",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = COLORS.teal;
              e.currentTarget.style.color = "#080C14";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = `${COLORS.teal}12`;
              e.currentTarget.style.color = COLORS.teal;
            }}
          >
            ↺ Rafraîchir l'analyse
          </button>
        )}
      </div>

      {/* ── Panneau IA ── */}
      <AIInsightsPanel
        data={data}
        loading={loading}
        streaming={streaming}
        rawText={rawText}
        error={error}
        onRefresh={() => fetchInsights(records, prediction, history)}
      />

      {/* ── Table OMS ── */}
      <SectionTitle>📋 Statistiques résumées vs seuils OMS</SectionTitle>
      <ChartCard delay={0}>
        <div style={{ overflowX: "auto" }}>
          <table style={{
            width: "100%",
            borderCollapse: "collapse",
            /* Héritage de la font — les td/th précisent la leur */
          }}>
            <thead>
              <tr style={{ background: "var(--surface2)" }}>
                {["Indicateur", "Valeur mesurée", "Seuil OMS", "Statut"].map((h) => (
                  <th key={h} style={thStyle}>{h}</th>
                ))}
              </tr>
            </thead>

            <tbody>
              {tableRows.map((row, i) => (
                <tr
                  key={row.label}
                  style={{
                    background: i % 2 === 0 ? "transparent" : "var(--surface2)",
                    transition: "background 0.1s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = `${COLORS.teal}08`)}
                  onMouseLeave={(e) => (e.currentTarget.style.background = i % 2 === 0 ? "transparent" : "var(--surface2)")}
                >
                  {/* Indicateur */}
                  <td style={{
                    ...tdBase,
                    fontFamily: "Outfit, sans-serif",
                    fontWeight: 500,
                    color: "var(--text)",
                  }}>
                    {row.label}
                  </td>

                  {/* Valeur — la plus importante, bien visible */}
                  <td style={{
                    ...tdBase,
                    fontFamily: "JetBrains Mono, monospace",
                    fontWeight: 700,
                    fontSize: 14,
                    color: COLORS.teal,
                    letterSpacing: "0.02em",
                  }}>
                    {row.value}
                  </td>

                  {/* Seuil OMS */}
                  <td style={{
                    ...tdBase,
                    fontFamily: "JetBrains Mono, monospace",
                    fontWeight: 500,
                    color: "var(--muted)",
                  }}>
                    {row.oms}
                  </td>

                  {/* Statut */}
                  <td style={{ ...tdBase }}>
                    {row.oms === "—" ? (
                      <span style={{ color: "var(--muted)", fontSize: 12 }}>—</span>
                    ) : (
                      <span style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 5,
                        fontSize: 12,
                        fontWeight: 700,
                        fontFamily: "Outfit, sans-serif",
                        padding: "3px 10px",
                        borderRadius: 20,
                        border: `1px solid ${row.ok ? COLORS.teal : COLORS.danger}40`,
                        background: row.ok ? `${COLORS.teal}12` : `${COLORS.danger}12`,
                        color: row.ok ? COLORS.teal : COLORS.danger,
                        whiteSpace: "nowrap",
                      }}>
                        {row.ok ? "✓" : "✗"}
                        {row.ok ? " Conforme" : " Dépassé"}
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