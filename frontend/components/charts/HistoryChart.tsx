"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer,
} from "recharts";
import { COLORS } from "@/lib/constants";

interface Props {
  dates: string[];
  values: number[];
}

export default function HistoryChart({ dates, values }: Props) {
  const data = dates.map((d, i) => ({ date: d.slice(5), value: values[i] }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: COLORS.muted, fontFamily: "JetBrains Mono" }} />
        <YAxis tick={{ fontSize: 11, fill: COLORS.muted, fontFamily: "JetBrains Mono" }} width={38} />
        <Tooltip
          formatter={(v: number) => [`${v.toFixed(2)} μg/m³`, "PM2.5"]}
          contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 8, fontFamily: "JetBrains Mono" }}
          labelStyle={{ color: COLORS.muted }}
        />
        <ReferenceLine y={15} stroke={COLORS.teal} strokeDasharray="4 4" label={{ value: "OMS", fill: COLORS.teal, fontSize: 10, position: "right" }} />
        <Line
          type="monotone"
          dataKey="value"
          stroke={COLORS.coral}
          strokeWidth={2.5}
          dot={{ r: 4, fill: COLORS.coral, strokeWidth: 0 }}
          activeDot={{ r: 6, fill: COLORS.coral }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}