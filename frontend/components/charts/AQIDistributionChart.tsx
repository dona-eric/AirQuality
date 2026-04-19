"use client";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
} from "recharts";
import { COLORS } from "@/lib/constants";

interface Props { 
  bon: number; 
  moyen: number; 
  mauvais: number;
}

const AQI_COLORS = [COLORS.teal, COLORS.amber, COLORS.danger];
const LABELS = ["Bon", "Modéré", "Mauvais"];

export default function AQIDistributionChart({ bon, moyen, mauvais }: Props) {
  const total = bon + moyen + mauvais || 1;
  const data = [
    { name: "Bon", value: +(bon / total * 100).toFixed(1), count: bon },
    { name: "Modéré", value: +(moyen / total * 100).toFixed(1), count: moyen },
    { name: "Mauvais", value: +(mauvais / total * 100).toFixed(1), count: mauvais },
  ];

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={true}
          label={(entry) => `${entry.name} ${entry.value}%`}
          outerRadius={60}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={AQI_COLORS[index % AQI_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value, name, props) => [
            `${value}% (${props.payload.count} heures)`,
            props.payload.name
          ]}
          contentStyle={{ background: "#111826", border: `1px solid ${COLORS.border}`, borderRadius: 6, fontSize: 11 }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}