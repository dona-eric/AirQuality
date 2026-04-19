"use client";
import { useState } from "react";
import type { AirRecord } from "@/lib/types";
import { COLORS, POLLUTANT_META } from "@/lib/constants";
import SectionTitle from "@/components/ui/SectionTitle";
import ChartCard from "@/components/ui/ChartCard";
import MapChart from "@/components/charts/MapChart";

interface Props { records: AirRecord[] }

export default function Mapping({ records }: Props) {
  const pollKeys = Object.keys(POLLUTANT_META);
  const [poll, setPoll] = useState<string>("pm2_5");

  return (
    <div>
      <SectionTitle>🌍 Cartographie temps réel</SectionTitle>
      
      {/* Selector */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
        {pollKeys.map((k) => {
          const m = POLLUTANT_META[k];
          const active = poll === k;
          return (
            <button key={k} onClick={() => setPoll(k)}
              style={{
                padding: "5px 12px",
                borderRadius: 20,
                border: `1px solid ${active ? m.color : COLORS.border}`,
                background: active ? `${m.color}18` : "transparent",
                color: active ? m.color : COLORS.muted,
                fontSize: 12,
                fontFamily: "JetBrains Mono, monospace",
                cursor: "pointer",
                transition: "all 0.15s",
              }}>
              {m.label}
            </button>
          );
        })}
      </div>

      <ChartCard 
        title={`Distribution spatiale : ${POLLUTANT_META[poll]?.label || poll}`}
        caption="Bulles : concentration du polluant"
        delay={0}>
        <MapChart records={records} pollutant={poll as keyof typeof POLLUTANT_META} />
      </ChartCard>
    </div>
  );
}
