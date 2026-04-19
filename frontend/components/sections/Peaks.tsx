"use client";
import type { DailyRow } from "@/lib/types";
import { COLORS } from "@/lib/constants";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard from "@/components/ui/ChartCard";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, Cell, ResponsiveContainer,
} from "recharts";

interface Props { daily: DailyRow[] }

interface Episode {
  debut: string; fin: string; duration: number; aqiMax: number; aqiMoy: number;
}

function detectEpisodes(daily: DailyRow[]): Episode[] {
  const episodes: Episode[] = [];
  let streak: DailyRow[] = [];
  for (const row of daily) {
    if (row.european_aqi > 60) {
      streak.push(row);
    } else {
      if (streak.length >= 3) {
        episodes.push({
          debut:   streak[0].date,
          fin:     streak[streak.length - 1].date,
          duration: streak.length,
          aqiMax:  +Math.max(...streak.map((r) => r.european_aqi)).toFixed(1),
          aqiMoy:  +(streak.reduce((s, r) => s + r.european_aqi, 0) / streak.length).toFixed(1),
        });
      }
      streak = [];
    }
  }
  return episodes.sort((a, b) => b.aqiMax - a.aqiMax);
}

export default function Peaks({ daily }: Props) {
  const top15 = [...daily]
    .sort((a, b) => b.european_aqi - a.european_aqi)
    .slice(0, 15)
    .map((r) => ({ date: r.date.slice(5), aqi: +r.european_aqi.toFixed(1) }));

  const episodes = detectEpisodes(daily);

  const barColor = (v: number) => v > 70 ? COLORS.danger : v > 55 ? COLORS.coral : COLORS.amber;

  return (
    <div>
      <SectionTitle>⚡ Épisodes de pollution prolongés (AQI &gt; 60 ≥ 3 jours)</SectionTitle>

      {episodes.length === 0 ? (
        <div style={{ color: COLORS.muted, fontFamily: "JetBrains Mono, monospace", fontSize: 13, padding: "20px 0" }}>
          Aucun épisode prolongé détecté sur la période.
        </div>
      ) : (
        <ChartCard delay={0}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {episodes.map((ep, i) => {
              const pct = Math.min((ep.aqiMax / 85) * 100, 100);
              const color = barColor(ep.aqiMax);
              return (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "180px 1fr 80px",
                  alignItems: "center", gap: 14,
                }}>
                  <div style={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace", color: COLORS.muted }}>
                    {ep.debut.slice(5)} → {ep.fin.slice(5)}
                    <span style={{ marginLeft: 6, color: COLORS.text }}>{ep.duration}j</span>
                  </div>
                  <div style={{ background: "var(--border)", borderRadius: 4, height: 16, overflow: "hidden", position: "relative" }}>
                    <div style={{
                      width: `${pct}%`, height: "100%", background: color,
                      borderRadius: 4, transition: "width 0.5s ease",
                      display: "flex", alignItems: "center", paddingLeft: 8,
                    }}>
                      <span style={{ fontSize: 10, color: "#fff", fontFamily: "JetBrains Mono, monospace", whiteSpace: "nowrap" }}>
                        AQI max {ep.aqiMax}
                      </span>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color, fontFamily: "JetBrains Mono, monospace", textAlign: "right" }}>
                    moy {ep.aqiMoy}
                  </div>
                </div>
              );
            })}
          </div>
        </ChartCard>
      )}

      <SectionTitle>🏆 Top 15 jours les plus pollués</SectionTitle>
      <ChartCard caption="AQI maximum journalier" delay={0}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={top15} margin={{ top: 8, right: 16, left: -10, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: COLORS.muted, fontFamily: "JetBrains Mono" }} angle={-40} textAnchor="end" />
            <YAxis tick={{ fontSize: 9, fill: COLORS.muted }} domain={[0, 95]} />
            <ReferenceLine y={60} stroke={COLORS.danger} strokeDasharray="4 4"
              label={{ value: "Seuil Très mauvais", fill: COLORS.danger, fontSize: 9, position: "insideTopRight" }} />
            <Tooltip
              formatter={(v: number) => [`${v}`, "AQI max"]}
              contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 8, fontSize: 11, fontFamily: "JetBrains Mono" }}
            />
            <Bar dataKey="aqi" radius={[4, 4, 0, 0]}>
              {top15.map((entry, i) => (
                <Cell key={i} fill={barColor(entry.aqi)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}