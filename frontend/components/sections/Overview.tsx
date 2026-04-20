"use client";
import type { AirRecord, DailyRow, HourlyRow, PredictionResponse, HistoryResponse } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import { getAqiLabel } from "@/lib/api";
import SectionTitle from "@/components/ui/SectionTitle";
import KPICard from "@/components/ui/KPICard";
import ChartCard from "@/components/ui/ChartCard";
import PredictionBanner from "@/components/PredictionBanner";
import OMSGauges from "@/components/charts/OMSGauges";
import AQIDistributionChart from "@/components/charts/AQIDistributionChart";
import MonthlyChart from "@/components/charts/MonthlyChart";
import HourlyChart from "@/components/charts/HourlyChart";
import PollutantGrid from "@/components/charts/PolluantsGrid";

interface Props {
  records: AirRecord[];
  daily: DailyRow[];
  hourly: HourlyRow[];
  pred: PredictionResponse | null;
  hist: HistoryResponse | null;
  loadingPred: boolean;
}

export default function Overview({ records, daily, hourly, pred, hist, loadingPred }: Props) {
  // Global stats
  const mean  = (col: keyof AirRecord) => {
    const vals = records.map((r) => r[col] as number).filter((v) => !isNaN(v));
    return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2) : 0;
  };
  const quant = (col: keyof AirRecord, q: number) => {
    const vals = records.map((r) => r[col] as number).filter((v) => !isNaN(v)).sort((a, b) => a - b);
    return vals[Math.floor(vals.length * q)] ?? 0;
  };

  const pm25Mean  = mean("pm2_5");
  const pm10Mean  = mean("pm10");
  const o3Mean    = mean("ozone");
  const no2Mean   = mean("nitrogen_dioxide");
  const aqiMean   = mean("european_aqi");
  const pm25P95   = quant("pm2_5", 0.95);
  const pmRatio   = +(pm25Mean / (pm10Mean || 1)).toFixed(2);

  // AQI label counts
  const aqiLevels = records.map((r) => getAqiLabel(r.pm2_5 as number));
  const total     = aqiLevels.length || 1;
  const bon       = aqiLevels.filter((l) => l === "Bon").length;
  const moyen     = aqiLevels.filter((l) => l === "Moyen").length;
  const mauvais   = aqiLevels.filter((l) => l === "Mauvais").length;
  const bonPct    = +((bon / total) * 100).toFixed(1);
  const moyenPct  = +((moyen / total) * 100).toFixed(1);
  const mauvaisPct= +((mauvais / total) * 100).toFixed(1);

  // OMS status
  const aqiColor  = aqiMean <= 50 ? COLORS.teal : aqiMean <= 100 ? COLORS.amber : COLORS.danger;
  const aqiStatus = aqiMean <= 50 ? "Bon" : aqiMean <= 100 ? "Modéré" : "Mauvais";

  return (
    <div>
      {/* ── Prévision IA */}
      <SectionTitle>🤖 Prévision IA à 24h</SectionTitle>
      <PredictionBanner pred={pred} hist={hist} loading={loadingPred} />

      {/* ── KPIs */}
      <SectionTitle>📊 Indicateurs clés — période complète</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 14, minWidth:0 }}>
        <KPICard title="AQI Moyen"     value={String(aqiMean)} subtitle={aqiStatus} color={aqiColor} delay={0}   />
        <KPICard title="PM2.5 Moyen"   value={`${pm25Mean} μg/m³`} subtitle={`P95 : ${pm25P95}`} color={COLORS.coral}  delay={50}  />
        <KPICard title="PM10 Moyen"    value={`${pm10Mean} μg/m³`} subtitle="Données 24h"  color={COLORS.amber}  delay={100} />
        <KPICard title="Rapport PM2.5/PM10" value={String(pmRatio)} subtitle="Source mixte biomasse/poussière" color={COLORS.violet} delay={150} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 , minWidth:0}}>
        <KPICard title="Ozone Moyen"    value={`${o3Mean} μg/m³`}   subtitle=""              color={COLORS.teal}   delay={200} />
        <KPICard title="Heures Mauvais" value={`${mauvaisPct}%`}    subtitle="AQI > 35.5"    color={COLORS.danger} delay={250} />
        <KPICard title="Niveau dominant"
          value={mauvaisPct > 50 ? "Mauvais" : moyenPct > 50 ? "Modéré" : "Bon"}
          subtitle={`Mauvais ${mauvaisPct}% · Modéré ${moyenPct}% · Bon ${bonPct}%`}
          color={COLORS.indigo} delay={300} />
        <KPICard title="Total mesures" value={records.length.toLocaleString("fr")} subtitle="enregistrements horaires" color={COLORS.muted} delay={350} />
      </div>

      {/* ── OMS Gauges */}
      <SectionTitle>⚖️ Dépassements des seuils OMS</SectionTitle>
      <ChartCard caption="Rouge = dépassement · Valeurs moyennes sur la période" delay={0}>
        <OMSGauges pm25={pm25Mean} pm10={pm10Mean} o3={o3Mean} no2={no2Mean} />
      </ChartCard>

      {/* ── Pollutant Glass Grid */}
      <SectionTitle>🧪 Détails des polluants — temps réel</SectionTitle>
      <PollutantGrid records={records} daily={daily} />

      {/* ── AQI Distribution + Monthly */}
      <SectionTitle>📊 Répartition AQI & Tendance mensuelle</SectionTitle>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <ChartCard title="Répartition des niveaux AQI" delay={0}>
          <AQIDistributionChart bon={bon} moyen={moyen} mauvais={mauvais} />
        </ChartCard>
        <ChartCard title="Évolution mensuelle comparative" delay={80}>
          <MonthlyChart daily={daily} />
        </ChartCard>
      </div>

      {/* ── Hourly profile */}
      <SectionTitle>⏰ Profil horaire moyen — cycle journalier</SectionTitle>
      <ChartCard caption="Analyse cyclique des 6 indicateurs sur 24 heures" delay={0}>
        <HourlyChart data={hourly} />
      </ChartCard>
    </div>
  );
}