import { useState, useCallback } from "react";
import type { AirRecord, PredictionResponse, HistoryResponse } from "@/lib/types";

export interface AIInsight {
  categorie: string;
  priorite: "haute" | "moyenne" | "basse";
  titre: string;
  texte: string;
  action: string;
}

export interface AIRecommendations {
  niveau_global: "Bon" | "Modéré" | "Mauvais" | "Très Mauvais";
  score_risque: number;
  resume: string;
  insights: AIInsight[];
  recommandations_population: {
    grand_public: string[];
    vulnerables: string[];
    activites_ext: string[];
  };
  prevision_commentaire: string;
  alerte: string | null;
}

function computeStats(records: AirRecord[]) {
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
  const o3 = vals("ozone");
  const no2 = vals("nitrogen_dioxide");
  const aqi = vals("european_aqi");

  const pm25Mean = mean(pm25);
  const pm10Mean = mean(pm10);

  // Pearson correlation PM2.5 / PM10
  const n = Math.min(pm25.length, pm10.length);
  const mx = mean(pm25.slice(0, n));
  const my = mean(pm10.slice(0, n));
  let num = 0, di = 0, dj = 0;
  for (let i = 0; i < n; i++) {
    const a = pm25[i] - mx, b = pm10[i] - my;
    num += a * b; di += a * a; dj += b * b;
  }
  const corrPm = di && dj ? +(num / Math.sqrt(di * dj)).toFixed(2) : 0;

  // AQI / PM2.5
  const aqiMeanV = mean(aqi);
  const pm25m = mean(pm25);
  let nAqiPm = 0, dAqi = 0, dPm = 0;
  const aqiSlice = aqi.slice(0, Math.min(aqi.length, pm25.length));
  const pm25Slice = pm25.slice(0, aqiSlice.length);
  const ma = mean(aqiSlice), mb = mean(pm25Slice);
  for (let i = 0; i < aqiSlice.length; i++) {
    const a = aqiSlice[i] - ma, b = pm25Slice[i] - mb;
    nAqiPm += a * b; dAqi += a * a; dPm += b * b;
  }
  const corrAqiPm25 = dAqi && dPm ? +(nAqiPm / Math.sqrt(dAqi * dPm)).toFixed(2) : 0;

  const month = new Date().getMonth() + 1;
  const isHarmattan = month >= 11 || month <= 2;
  const monthNames: Record<number, string> = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
  };

  return {
    pm25Mean,
    pm10Mean,
    o3Mean: mean(o3),
    no2Mean: mean(no2),
    aqiMean: aqiMeanV,
    pm25P95: q95(pm25),
    pmRatio: pm10Mean ? +(pm25Mean / pm10Mean).toFixed(2) : 0,
    mauvaisPct: pct(pm25, 35.5),
    tresMauvaisPct: pct(aqi, 60),
    totalRecords: records.length,
    corrPm,
    corrAqiPm25,
    moisActuel: monthNames[month],
    isHarmattan,
  };
}

export function useAIInsights() {
  const [data, setData] = useState<AIRecommendations | null>(null);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(
    async (
      records: AirRecord[],
      prediction: PredictionResponse | null,
      history: HistoryResponse | null
    ) => {
      if (!records.length) return;
      setLoading(true);
      setStreaming(true);
      setRawText("");
      setData(null);
      setError(null);

      try {
        const stats = computeStats(records);
        const res = await window.fetch("/api/ai-insight",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ stats, prediction, history }),
        });

        if (!res.ok) throw new Error(`Erreur API: ${res.status}`);
        if (!res.body) throw new Error("Stream body vide");

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          accumulated += chunk;
          setRawText(accumulated);
        }

        // Parse JSON from accumulated text
        const cleaned = accumulated
          .replace(/```json\s*/g, "")
          .replace(/```\s*/g, "")
          .trim();
        const parsed: AIRecommendations = JSON.parse(cleaned);
        setData(parsed);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
        setStreaming(false);
      }
    },
    []
  );

  return { data, loading, streaming, rawText, error, fetch };
}