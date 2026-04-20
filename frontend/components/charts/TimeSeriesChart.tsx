"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot } from "recharts";
import type { DailyRow } from "@/lib/types";
import { COLORS, POLLUTANT_META } from "@/lib/constants";

interface Props {
  daily: DailyRow[];
  anomalyDates?: Set<string>;
  pollutant?: keyof typeof POLLUTANT_META;
}

export default function TimeSeriesChart({ daily, anomalyDates = new Set(), pollutant = "pm2_5" }: Props) {
  const pollutantKey = pollutant as keyof DailyRow;
  const meta = POLLUTANT_META[pollutant] || { label: pollutant, unit: "", color: COLORS.muted };

  const data = daily.map((row) => ({
    date: row.date.slice(5),
    value: row[pollutantKey] as number,
    isAnomaly: anomalyDates.has(row.date.slice(0, 10)),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: COLORS.muted, fontFamily: "JetBrains Mono" }} />
        <YAxis tick={{ fontSize: 10, fill: COLORS.muted }} label={{ value: meta.unit, angle: -90, position: "insideLeft" }} />
        <Tooltip
          contentStyle={{ background: "#111826", borderRadius: 8, fontSize: 11, fontFamily: "JetBrains Mono" }}
          labelStyle={{ color: COLORS.text }}
          formatter={(value: any) => value.toFixed(2)}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke={meta.color} 
          dot={false} 
          strokeWidth={2} 
          name={meta.label}
          isAnimationActive={false}
        />
        {data.map((point, idx) => 
          point.isAnomaly ? (
            <ReferenceDot 
              key={idx} 
              x={point.date} 
              y={point.value} 
              r={4} 
              fill={COLORS.danger} 
              stroke="white" 
              strokeWidth={2}
            />
          ) : null
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}