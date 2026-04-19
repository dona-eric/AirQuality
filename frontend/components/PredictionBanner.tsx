"use client";
import type { PredictionResponse, HistoryResponse } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import HistoryChart from "@/components/charts/HistoryChart";
import KPICard from "@/components/ui/KPICard";

interface Props {
  pred: PredictionResponse | null;
  hist: HistoryResponse | null;
  loading: boolean;
}

export default function PredictionBanner({ pred, hist, loading }: Props) {
  if (loading) {
    return (
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, color: COLORS.muted, fontFamily: "JetBrains Mono, monospace", fontSize: 13 }}>
          <div className="live-dot" />
          Chargement des prévisions IA…
        </div>
      </div>
    );
  }

  if (!pred) {
    return (
      <div style={{ background: "var(--surface)", border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 20 }}>
        <span style={{ fontSize: 13, color: COLORS.muted }}>
          💡 API non disponible — vérifiez l'endpoint dans la barre latérale.
        </span>
      </div>
    );
  }

  const isGood    = pred.aqi_label === "Bon";
  const isBad     = pred.aqi_label.includes("Mauvais");
  const alertBg   = isBad ? "rgba(239,68,68,0.07)" : isGood ? "rgba(13,148,136,0.07)" : "rgba(245,158,11,0.07)";
  const alertBorder = isBad ? COLORS.danger : isGood ? COLORS.teal : COLORS.amber;
  const deltaSign = (pred.delta ?? 0) > 0 ? "↑" : "↓";

  return (
    <div>
      {/* KPI row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginBottom: 14 }}>
        <KPICard
          title="PM2.5 Actuel"
          value={`${pred.current_pm25} μg/m³`}
          subtitle="Mesure la plus récente"
          color={COLORS.danger}
          delay={0}
        />
        <KPICard
          title="Prévision J+1"
          value={`${pred.predicted_pm25} μg/m³`}
          subtitle={`${deltaSign} ${Math.abs(pred.delta ?? 0)} μg/m³ vs actuel · ${pred.date_prevision}`}
          color={COLORS.indigo}
          delay={50}
        />
        <KPICard
          title="Statut prévu"
          value={pred.aqi_label}
          subtitle={pred.conseil}
          color={isBad ? COLORS.danger : isGood ? COLORS.teal : COLORS.amber}
          delay={100}
        />
      </div>

      {/* Alert strip */}
      <div style={{
        background: alertBg,
        borderLeft: `3px solid ${alertBorder}`,
        borderRadius: "0 8px 8px 0",
        padding: "10px 16px",
        marginBottom: 16,
        fontSize: 13,
        color: alertBorder,
        fontFamily: "Outfit, sans-serif",
      }}>
        {isBad
          ? "⚠️ Pic de pollution prévu. Pensez à limiter vos trajets en Zémidjan demain."
          : isGood
          ? "✅ L'air sera de bonne qualité demain. Idéal pour une sortie sur la Route des Pêches !"
          : "🟡 Qualité modérée prévue. Les personnes sensibles devraient limiter les efforts prolongés."}
      </div>

      {/* History sparkline */}
      {hist && (
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 18px" }}>
          <div style={{ fontFamily: "Syne, sans-serif", fontWeight: 700, fontSize: 13, color: "var(--text)", marginBottom: 12 }}>
            Historique — 7 derniers jours
          </div>
          <HistoryChart dates={hist.dates} values={hist.values} />
        </div>
      )}
    </div>
  );
}