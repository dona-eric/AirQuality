"use client";
import { useMemo } from "react";
import {
  AreaChart, Area, ResponsiveContainer, Tooltip,
} from "recharts";
import type { AirRecord, DailyRow } from "@/lib/types";

// ─────────────────────────────────────────────
//  DESIGN TOKENS — cohérents avec globals.css
// ─────────────────────────────────────────────
const T = {
  glass:     "rgba(255,255,255,0.06)",
  border:    "rgba(255,255,255,0.12)",
  borderHi:  "rgba(255,255,255,0.20)",
  textPrim:  "#FFFFFF",
  textMuted: "#8896B0",
  good:      "#00E5B4",
  warn:      "#F59E0B",
  bad:       "#EF4444",
  indigo:    "#6366F1",
  violet:    "#8B5CF6",
  bg:        "#080C14",
};

// ─────────────────────────────────────────────
//  POLLUANT METADATA
// ─────────────────────────────────────────────
interface PollutantDef {
  key:        string;          // clé dans AirRecord
  label:      string;          // affiché
  unit:       string;
  omsGood:    number;          // ≤ → Bon
  omsWarn:    number;          // ≤ → Modéré  |  > → Mauvais
  icon:       React.ReactNode;
}

const POLLUTANTS: PollutantDef[] = [
  {
    key: "pm2_5", label: "PM₂.₅", unit: "μg/m³",
    omsGood: 12,  omsWarn: 35.5,
    icon: <IconPM size={15} />,
  },
  {
    key: "pm10",  label: "PM₁₀",  unit: "μg/m³",
    omsGood: 40,  omsWarn: 75,
    icon: <IconPM size={15} />,
  },
  {
    key: "nitrogen_dioxide", label: "NO₂", unit: "μg/m³",
    omsGood: 10,  omsWarn: 25,
    icon: <IconMolecule size={15} />,
  },
  {
    key: "ozone", label: "O₃", unit: "μg/m³",
    omsGood: 100, omsWarn: 140,
    icon: <IconO3 size={15} />,
  },
  {
    key: "sulphur_dioxide", label: "SO₂", unit: "μg/m³",
    omsGood: 40,  omsWarn: 80,
    icon: <IconMolecule size={15} />,
  },
  {
    key: "carbon_monoxide", label: "CO",  unit: "μg/m³",
    omsGood: 4000, omsWarn: 10000,
    icon: <IconMolecule size={15} />,
  },
];

// ─────────────────────────────────────────────
//  ICÔNES SVG INLINE LÉGÈRES
// ─────────────────────────────────────────────
function IconPM({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
      <circle cx="12" cy="12" r="3" />
      <circle cx="5"  cy="6"  r="2" opacity={0.6} />
      <circle cx="19" cy="7"  r="1.5" opacity={0.5} />
      <circle cx="7"  cy="18" r="1.5" opacity={0.5} />
      <circle cx="17" cy="17" r="2"   opacity={0.7} />
    </svg>
  );
}

function IconMolecule({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
      <circle cx="12" cy="12" r="2.5" />
      <circle cx="5"  cy="5"  r="2"   />
      <circle cx="19" cy="5"  r="2"   />
      <circle cx="12" cy="20" r="2"   />
      <line x1="7"  y1="7"  x2="10.5" y2="10.5" />
      <line x1="17" y1="7"  x2="13.5" y2="10.5" />
      <line x1="12" y1="14.5" x2="12" y2="18"   />
    </svg>
  );
}

function IconO3({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
      <path d="M12 3C7 3 3 7 3 12s4 9 9 9 9-4 9-9" strokeDasharray="4 2" />
      <circle cx="12" cy="12" r="3" />
      <path d="M16 4 Q20 8 20 12" />
    </svg>
  );
}

// ─────────────────────────────────────────────
//  STATUS HELPER
// ─────────────────────────────────────────────
interface Status {
  label: string;
  color: string;
  glow:  string | null;
}

function getStatus(value: number, def: PollutantDef): Status {
  if (value <= def.omsGood) return { label: "Bon",    color: T.good, glow: null };
  if (value <= def.omsWarn) return { label: "Modéré", color: T.warn, glow: null };
  return {
    label: "Mauvais",
    color: T.bad,
    glow:  "0 0 60px 12px rgba(239,68,68,0.25), 0 0 120px 30px rgba(239,68,68,0.10)",
  };
}

// ─────────────────────────────────────────────
//  MINI SPARKLINE
// ─────────────────────────────────────────────
interface SparkProps {
  data:   { v: number }[];
  color:  string;
  label:  string;
}

function Sparkline({ data, color, label }: SparkProps) {
  const gradId = `sg-${label.replace(/[^a-z]/gi, "")}`;
  return (
    <div style={{ width: "100%", height: 52, marginTop: 2 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0}    />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={1.8}
            fill={`url(#${gradId})`}
            dot={false}
            isAnimationActive={false}
          />
          <Tooltip
            content={({ active, payload }) =>
              active && payload?.length ? (
                <div style={{
                  background: "rgba(8,12,20,0.92)",
                  border: `1px solid ${T.border}`,
                  borderRadius: 6,
                  padding: "4px 9px",
                  fontSize: 11,
                  color: color,
                  fontFamily: "JetBrains Mono, monospace",
                }}>
                  {(payload[0].value as number).toFixed(2)}
                </div>
              ) : null
            }
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─────────────────────────────────────────────
//  SINGLE POLLUTANT CARD
// ─────────────────────────────────────────────
interface CardProps {
  def:        PollutantDef;
  value:      number;
  sparkData:  { v: number }[];
  delay:      number;
}

function PollutantCard({ def, value, sparkData, delay }: CardProps) {
  const status = getStatus(value, def);
  const trend  = sparkData.length >= 2
    ? sparkData[sparkData.length - 1].v - sparkData[0].v
    : 0;
  const trendSign = trend > 0.5 ? "↑" : trend < -0.5 ? "↓" : "→";
  const trendColor = trend > 0.5
    ? (status.color === T.good ? T.warn : status.color)
    : T.good;

  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        position:       "relative",
        background:     T.glass,
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        border:         `1px solid ${status.glow ? "rgba(239,68,68,0.35)" : T.border}`,
        borderRadius:   20,
        padding:        "18px 18px 14px",
        display:        "flex",
        flexDirection:  "column",
        gap:            10,
        transition:     "transform 0.2s ease, box-shadow 0.2s ease",
        boxShadow:      status.glow ?? "0 4px 24px rgba(0,0,0,0.3)",
        cursor:         "default",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateY(-3px)";
        (e.currentTarget as HTMLDivElement).style.boxShadow =
          status.glow
            ? "0 0 80px 20px rgba(239,68,68,0.30), 0 8px 32px rgba(0,0,0,0.4)"
            : "0 8px 32px rgba(0,0,0,0.4)";
        (e.currentTarget as HTMLDivElement).style.borderColor =
          status.glow ? "rgba(239,68,68,0.5)" : T.borderHi;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
        (e.currentTarget as HTMLDivElement).style.boxShadow =
          status.glow ?? "0 4px 24px rgba(0,0,0,0.3)";
        (e.currentTarget as HTMLDivElement).style.borderColor =
          status.glow ? "rgba(239,68,68,0.35)" : T.border;
      }}
    >
      {/* ── HEADER ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        {/* Icône + Nom */}
        <div style={{ display: "flex", alignItems: "center", gap: 7, color: T.textMuted }}>
          {def.icon}
          <span
            style={{
              fontFamily:    "Syne, sans-serif",
              fontWeight:    600,
              fontSize:      13,
              color:         T.textMuted,
              letterSpacing: "0.02em",
            }}
          >
            {def.label}
          </span>
        </div>

        {/* Pastille état */}
        <div
          title={status.label}
          style={{
            width:        10,
            height:       10,
            borderRadius: "50%",
            background:   status.color,
            flexShrink:   0,
            boxShadow:    `0 0 8px 2px ${status.color}60`,
          }}
        />
      </div>

      {/* ── BODY — Trend label + valeur + unité ── */}
      <div style={{ textAlign: "center" }}>
        {/* Trend label */}
        <div
          style={{
            fontSize:      11,
            fontWeight:    700,
            fontFamily:    "JetBrains Mono, monospace",
            color:         status.color,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom:  4,
          }}
        >
          <span style={{ color: trendColor, marginRight: 4 }}>{trendSign}</span>
          {status.label}
        </div>

        {/* Valeur numérique */}
        <div
          style={{
            fontFamily:    "Syne, sans-serif",
            fontWeight:    800,
            fontSize:      30,
            color:         T.textPrim,
            lineHeight:    1,
            letterSpacing: "-0.03em",
          }}
        >
          {value >= 1000
            ? (value / 1000).toFixed(1) + "k"
            : value.toFixed(value < 10 ? 2 : 1)}
        </div>

        {/* Unité */}
        <div
          style={{
            fontSize:   11,
            fontWeight: 500,
            color:      T.textMuted,
            marginTop:  3,
            fontFamily: "JetBrains Mono, monospace",
          }}
        >
          {def.unit}
          <span
            style={{
              marginLeft:  8,
              fontSize:    10,
              color:       T.textMuted,
              opacity:     0.65,
            }}
          >
            OMS {def.omsGood}
          </span>
        </div>
      </div>

      {/* ── FOOTER — Sparkline ── */}
      <div>
        <Sparkline data={sparkData} color={status.color} label={def.label} />
        <div
          style={{
            display:        "flex",
            justifyContent: "space-between",
            marginTop:      4,
            fontSize:       9,
            fontFamily:     "JetBrains Mono, monospace",
            color:          T.textMuted,
            opacity:        0.6,
          }}
        >
          <span>14j</span>
          <span>Aujourd'hui</span>
        </div>
      </div>

      {/* OMS progress bar */}
      <div
        style={{
          height:        3,
          background:    "rgba(255,255,255,0.08)",
          borderRadius:  2,
          overflow:      "hidden",
        }}
      >
        <div
          style={{
            height:        "100%",
            width:         `${Math.min((value / (def.omsWarn * 1.4)) * 100, 100)}%`,
            background:    `linear-gradient(90deg, ${T.good}, ${status.color})`,
            borderRadius:  2,
            transition:    "width 1s ease",
          }}
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  GRID WRAPPER
// ─────────────────────────────────────────────
interface Props {
  records: AirRecord[];
  daily:   DailyRow[];
}

export default function PollutantGrid({ records, daily }: Props) {
  // Calcule la moyenne sur les 48 derniers enregistrements (≈ 2 derniers jours)
  const recentRecords = records.slice(-48);

  const currentValues = useMemo(() => {
    const avg = (col: string) => {
      const vals = recentRecords
        .map((r) => r[col] as number)
        .filter((v) => v != null && !isNaN(v));
      return vals.length
        ? +(vals.reduce((s, v) => s + v, 0) / vals.length).toFixed(3)
        : 0;
    };
    return {
      pm2_5:            avg("pm2_5"),
      pm10:             avg("pm10"),
      nitrogen_dioxide: avg("nitrogen_dioxide"),
      ozone:            avg("ozone"),
      sulphur_dioxide:  avg("sulphur_dioxide"),
      carbon_monoxide:  avg("carbon_monoxide"),
    };
  }, [recentRecords]);

  // Sparklines : 14 derniers jours de données journalières
  const sparkData = useMemo(() => {
    const last14 = daily.slice(-14);
    const build = (col: keyof DailyRow) =>
      last14.map((d) => ({ v: +(d[col] as number || 0) }));
    return {
      pm2_5:            build("pm2_5"),
      pm10:             build("pm10"),
      nitrogen_dioxide: build("nitrogen_dioxide"),
      ozone:            build("ozone"),
      sulphur_dioxide:  build("sulphur_dioxide"),
      carbon_monoxide:  build("carbon_monoxide"),
    };
  }, [daily]);

  return (
    <div>
      {/* En-tête de section */}
      <div
        style={{
          display:        "flex",
          alignItems:     "center",
          justifyContent: "space-between",
          marginBottom:   16,
        }}
      >
        <div>
          <div
            style={{
              fontFamily:    "Syne, sans-serif",
              fontWeight:    800,
              fontSize:      15,
              color:         "#C8D4E8",
              letterSpacing: "-0.01em",
            }}
          >
            Détails des Polluants
          </div>
          <div
            style={{
              fontSize:   11,
              color:      T.textMuted,
              fontFamily: "JetBrains Mono, monospace",
              marginTop:  3,
            }}
          >
            Moyenne 48h · sparkline 14 jours · seuils OMS
          </div>
        </div>

        {/* Légende des états */}
        <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
          {[
            { label: "Bon",     color: T.good },
            { label: "Modéré", color: T.warn },
            { label: "Mauvais", color: T.bad  },
          ].map(({ label, color }) => (
            <div
              key={label}
              style={{ display: "flex", alignItems: "center", gap: 5 }}
            >
              <div
                style={{
                  width:        7,
                  height:       7,
                  borderRadius: "50%",
                  background:   color,
                  boxShadow:    `0 0 5px ${color}`,
                }}
              />
              <span
                style={{
                  fontSize:   10,
                  color:      T.textMuted,
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Grille 6 cartes */}
      <div
        style={{
          display:               "grid",
          gridTemplateColumns:   "repeat(auto-fit, minmax(168px, 1fr))",
          gap:                   16,
          minWidth: 0
        }}
      >
        {POLLUTANTS.map((def, i) => (
          <PollutantCard
            key={def.key}
            def={def}
            value={currentValues[def.key as keyof typeof currentValues] ?? 0}
            sparkData={sparkData[def.key as keyof typeof sparkData] ?? []}
            delay={i * 70}
          />
        ))}
      </div>
    </div>
  );
}