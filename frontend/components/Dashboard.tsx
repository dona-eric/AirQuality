"use client";
import { useState, useEffect, useCallback } from "react";
import type { AirRecord, DailyRow, HourlyRow, PredictionResponse, HistoryResponse, PageId } from "@/lib/types";
import { API_BASE } from "@/lib/constants";
import { fetchPrediction, fetchHistory, fetchAllData, aggregateDaily, aggregateHourly } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";
import Sidebar       from "@/components/layout/Sidebar";
import Overview      from "@/components/sections/Overview";
import TimeSeries    from "@/components/sections/TimeSeries";
import Distributions from "@/components/sections/Distributions";
import Correlations  from "@/components/sections/Correlations";
import Peaks         from "@/components/sections/Peaks";
import MLInsights    from "@/components/sections/MLInsights";

export default function Dashboard() {
  const { theme, toggle } = useTheme();

  const [page, setPage]         = useState<PageId>("overview");
  const [apiUrl, setApiUrl]     = useState(API_BASE);
  const [records, setRecords]   = useState<AirRecord[]>([]);
  const [daily, setDaily]       = useState<DailyRow[]>([]);
  const [hourly, setHourly]     = useState<HourlyRow[]>([]);
  const [pred, setPred]         = useState<PredictionResponse | null>(null);
  const [hist, setHist]         = useState<HistoryResponse | null>(null);
  const [loading, setLoading]   = useState(true);
  const [loadingPred, setLoadingPred] = useState(true);
  const [error, setError]       = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await fetchAllData();
      if (!data) throw new Error("API inaccessible");
      const recs = data.records;
      setRecords(recs);
      setDaily(aggregateDaily(recs));
      setHourly(aggregateHourly(recs));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPrediction = useCallback(async () => {
    setLoadingPred(true);
    const [p, h] = await Promise.all([fetchPrediction(), fetchHistory()]);
    setPred(p); setHist(h);
    setLoadingPred(false);
  }, []);

  useEffect(() => { loadData(); loadPrediction(); }, [loadData, loadPrediction]);

  const handleRefresh = () => { loadData(); loadPrediction(); };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)" }}>
      <Sidebar
        active={page}
        onChange={setPage}
        apiUrl={apiUrl}
        onApiChange={setApiUrl}
        onRefresh={handleRefresh}
        theme={theme}
        onThemeToggle={toggle}
      />

      <main style={{
        flex: 1,
        minWidth: 0,
        padding: "28px 32px 60px",
        overflowX: "hidden",
        background: "var(--bg)",
      }}>
        {/* ── Header ── */}
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 14,
          padding: "20px 26px",
          marginBottom: 26,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "var(--shadow-sm)",
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{
                fontFamily: "Syne, sans-serif", fontWeight: 800,
                fontSize: 26, color: "#4285F4", letterSpacing: "0.03em",
              }}>
                AQI
              </span>
              <span style={{
                color: "var(--muted)", fontSize: 12,
                fontFamily: "JetBrains Mono, monospace",
              }}>
                PM2.5 & PM10 · Cotonou, Bénin
              </span>
            </div>
            <h1 style={{
              fontFamily: "Syne, sans-serif", fontWeight: 700,
              fontSize: 17, color: "var(--text)",
              margin: "4px 0 0", letterSpacing: "0.015em",
            }}>
              Indice de Qualité de l'Air · Littoral
            </h1>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div className="live-dot" />
            <span style={{
              fontSize: 11, color: "var(--muted)",
              fontFamily: "JetBrains Mono, monospace",
            }}>
              {loading
                ? "Chargement…"
                : `${records.length.toLocaleString("fr")} mesures`}
            </span>
          </div>
        </div>

        {/* ── Erreur ── */}
        {error && (
          <div style={{
            background: "rgba(239,68,68,0.07)",
            border: "1px solid var(--danger)",
            borderRadius: 10, padding: "12px 16px",
            marginBottom: 20, fontSize: 13,
            color: "var(--danger)",
            fontFamily: "JetBrains Mono, monospace",
          }}>
            ⚠ {error} — Vérifiez l'endpoint API ou le réseau.
          </div>
        )}

        {/* ── Skeleton ── */}
        {loading && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="skeleton"
                style={{
                  height: 88,
                  animationDelay: `${i * 0.08}s`,
                }}
              />
            ))}
          </div>
        )}

        {/* ── Pages ── */}
        {!loading && records.length > 0 && (
          <>
            {page === "overview"      && <Overview records={records} daily={daily} hourly={hourly} pred={pred} hist={hist} loadingPred={loadingPred} />}
            {page === "timeseries"    && <TimeSeries records={records} daily={daily} />}
            {page === "distributions" && <Distributions records={records} />}
            {page === "correlations"  && <Correlations records={records} />}
            {page === "peaks"         && <Peaks daily={daily} />}
            {page === "ml"            && <MLInsights records={records} prediction={pred} history={hist} />}
          </>
        )}
      </main>
    </div>
  );
}