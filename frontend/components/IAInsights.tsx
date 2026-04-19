"use client";
import { useEffect, useRef } from "react";
import type { AIRecommendations, AIInsight } from "@/lib/useiainsights";
import { COLORS } from "@/lib/constants";

// ── Helpers ───────────────────────────────────────────────────

const NIVEAU_COLOR: Record<string, string> = {
  Bon:           COLORS.teal,
  Modéré:        COLORS.amber,
  Mauvais:       COLORS.coral,
  "Très Mauvais": COLORS.danger,
};

const PRIO_COLOR: Record<string, string> = {
  haute:   COLORS.danger,
  moyenne: COLORS.amber,
  basse:   COLORS.teal,
};

const CAT_ICON: Record<string, string> = {
  "Feature ML":   "⚙",
  "Santé":        "🫁",
  "Tendance":     "📈",
  "Anomalie":     "⚠",
  "Saisonnalité": "🌬",
};

// ── Score gauge (SVG arc) ─────────────────────────────────────

function RiskGauge({ score }: { score: number }) {
  const pct   = score / 100;
  const r     = 44;
  const cx    = 56;
  const cy    = 56;
  const start = -140;
  const sweep = 280;
  const ang   = start + pct * sweep;

  const toXY = (deg: number) => ({
    x: cx + r * Math.cos((deg * Math.PI) / 180),
    y: cy + r * Math.sin((deg * Math.PI) / 180),
  });

  const arcPath = (a: number, b: number) => {
    const s = toXY(a), e = toXY(b);
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${b - a > 180 ? 1 : 0} 1 ${e.x} ${e.y}`;
  };

  const color =
    score < 30 ? COLORS.teal :
    score < 60 ? COLORS.amber :
    score < 80 ? COLORS.coral : COLORS.danger;

  return (
    <svg width={112} height={90} viewBox="0 0 112 90">
      <path d={arcPath(start, start + sweep)} fill="none" stroke="#1A2438" strokeWidth={10} strokeLinecap="round" />
      <path d={arcPath(start, ang)}           fill="none" stroke={color}    strokeWidth={10} strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={toXY(ang).x} y2={toXY(ang).y} stroke={color} strokeWidth={2.5} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={4} fill={color} />
      <text x={cx} y={cy + 18} textAnchor="middle" fontSize={20} fontWeight={800}
        fill={color} fontFamily="Syne, sans-serif">{score}</text>
      <text x={cx} y={cy + 30} textAnchor="middle" fontSize={9}
        fill={COLORS.muted} fontFamily="JetBrains Mono, monospace">/ 100</text>
    </svg>
  );
}

// ── Streaming cursor ──────────────────────────────────────────

function StreamCursor() {
  return (
    <span style={{
      display: "inline-block", width: 2, height: 14,
      background: COLORS.teal, marginLeft: 4, verticalAlign: "middle",
      animation: "pulse-dot 0.8s ease-in-out infinite",
    }} />
  );
}

// ── Individual insight card ───────────────────────────────────

function InsightCard({ ins, delay }: { ins: AIInsight; delay: number }) {
  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        background: "var(--surface)",
        border: `1px solid ${COLORS.border}`,
        borderLeft: `3px solid ${PRIO_COLOR[ins.priorite]}`,
        borderRadius: "0 10px 10px 0",
        padding: "14px 18px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 15 }}>{CAT_ICON[ins.categorie] ?? "●"}</span>
        <span style={{
          fontSize: 12, fontFamily: "JetBrains Mono, monospace",
          color: PRIO_COLOR[ins.priorite], textTransform: "uppercase",
          letterSpacing: "0.1em", fontWeight: 700,
        }}>
          {ins.categorie} · {ins.priorite}
        </span>
      </div>
      <div style={{
        fontFamily: "Syne, sans-serif", fontWeight: 700, fontSize: 13,
        color: "var(--text)", marginBottom: 6,
      }}>
        {ins.titre}
      </div>
      <p style={{ fontSize: 12, color: COLORS.muted, lineHeight: 1.65, margin: "0 0 8px" }}>
        {ins.texte}
      </p>
      <div style={{
        display: "flex", alignItems: "flex-start", gap: 6,
        background: `${PRIO_COLOR[ins.priorite]}10`,
        border: `1px solid ${PRIO_COLOR[ins.priorite]}30`,
        borderRadius: 6, padding: "7px 10px",
      }}>
        <span style={{ color: PRIO_COLOR[ins.priorite], fontSize: 11 }}>→</span>
        <span style={{ fontSize: 11, color: "var(--text)", fontFamily: "Outfit, sans-serif", lineHeight: 1.5 }}>
          {ins.action}
        </span>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────

interface Props {
  data: AIRecommendations | null;
  loading: boolean;
  streaming: boolean;
  rawText: string;
  error: string | null;
  onRefresh: () => void;
}

export default function AIInsightsPanel({
  data, loading, streaming, rawText, error, onRefresh,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll during streaming
  useEffect(() => {
    if (streaming && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [rawText, streaming]);

  // ── Loading / streaming state ──
  if (loading || (streaming && !data)) {
    return (
      <div style={{
        background: "var(--surface)", border: `1px solid ${COLORS.border}`,
        borderRadius: 12, padding: 24,
      }}>
        {/* Skeleton header */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
          <div style={{ width: 112, height: 90, background: "#1A2438", borderRadius: 8, flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ height: 16, width: "60%", background: "#1A2438", borderRadius: 4, marginBottom: 8 }} />
            <div style={{ height: 12, width: "90%", background: "#1A2438", borderRadius: 4, marginBottom: 6 }} />
            <div style={{ height: 12, width: "75%", background: "#1A2438", borderRadius: 4 }} />
          </div>
        </div>

        {/* Streaming raw text preview */}
        {rawText && (
          <div
            ref={scrollRef}
            style={{
              background: "#0B1018", border: `1px solid ${COLORS.border}`,
              borderRadius: 8, padding: "12px 16px", maxHeight: 160, overflowY: "auto",
              fontFamily: "JetBrains Mono, monospace", fontSize: 11,
              color: COLORS.muted, lineHeight: 1.6,
              whiteSpace: "pre-wrap", wordBreak: "break-word",
            }}
          >
            {rawText}
            <StreamCursor />
          </div>
        )}

        {!rawText && (
          <div style={{ display: "flex", alignItems: "center", gap: 10, color: COLORS.muted, fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>
            <div className="live-dot" />
            Analyse des données en cours par l'IA…
          </div>
        )}
      </div>
    );
  }

  // ── Error state ──
  if (error) {
    return (
      <div style={{
        background: "rgba(239,68,68,0.06)", border: `1px solid ${COLORS.danger}`,
        borderRadius: 12, padding: 20,
      }}>
        <div style={{ fontSize: 13, color: COLORS.danger, fontFamily: "JetBrains Mono, monospace", marginBottom: 10 }}>
          ⚠ Erreur lors de l'analyse IA : {error}
        </div>
        <button onClick={onRefresh} style={{
          background: "rgba(239,68,68,0.1)", border: `1px solid ${COLORS.danger}`,
          borderRadius: 6, color: COLORS.danger, padding: "6px 14px",
          fontSize: 12, fontFamily: "Outfit, sans-serif", cursor: "pointer",
        }}>
          Réessayer
        </button>
      </div>
    );
  }

  // ── Empty state ──
  if (!data) {
    return (
      <div style={{
        background: "var(--surface)", border: `1px dashed ${COLORS.border}`,
        borderRadius: 12, padding: 32, textAlign: "center",
      }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
        <div style={{ fontSize: 13, color: COLORS.muted, marginBottom: 16 }}>
          Aucune analyse générée. Cliquez pour lancer l'analyse IA.
        </div>
        <button onClick={onRefresh} style={{
          background: `${COLORS.teal}15`, border: `1px solid ${COLORS.teal}`,
          borderRadius: 8, color: COLORS.teal, padding: "9px 20px",
          fontSize: 13, fontFamily: "Outfit, sans-serif", cursor: "pointer",
          fontWeight: 600,
        }}>
          Lancer l'analyse →
        </button>
      </div>
    );
  }

  // ── Populated state ──
  const niveauColor = NIVEAU_COLOR[data.niveau_global] ?? COLORS.muted;

  return (
    <div>
      {/* Alerte urgente */}
      {data.alerte && (
        <div className="fade-up" style={{
          background: "rgba(239,68,68,0.08)", border: `1px solid ${COLORS.danger}`,
          borderLeft: `4px solid ${COLORS.danger}`, borderRadius: "0 10px 10px 0",
          padding: "12px 18px", marginBottom: 16,
          display: "flex", alignItems: "center", gap: 10,
        }}>
          <span style={{ fontSize: 18 }}>🚨</span>
          <span style={{ fontSize: 13, color: COLORS.danger, fontFamily: "Outfit, sans-serif", lineHeight: 1.5 }}>
            {data.alerte}
          </span>
        </div>
      )}

      {/* En-tête — Score + Résumé */}
      <div className="fade-up" style={{
        background: "var(--surface)", border: `1px solid ${COLORS.border}`,
        borderRadius: 12, padding: "20px 24px", marginBottom: 14,
        display: "grid", gridTemplateColumns: "auto 1fr", gap: 24, alignItems: "center",
      }}>
        <div style={{ textAlign: "center" }}>
          <RiskGauge score={data.score_risque} />
          <div style={{
            fontSize: 11, fontFamily: "JetBrains Mono, monospace",
            color: COLORS.muted, marginTop: 4,
          }}>
            Score de risque
          </div>
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <span style={{
              fontSize: 11, fontWeight: 700, fontFamily: "JetBrains Mono, monospace",
              color: niveauColor, textTransform: "uppercase", letterSpacing: "0.12em",
              background: `${niveauColor}15`, padding: "3px 10px", borderRadius: 20,
              border: `1px solid ${niveauColor}40`,
            }}>
              {data.niveau_global}
            </span>
            <button
              onClick={onRefresh}
              title="Relancer l'analyse"
              style={{
                background: "transparent", border: `1px solid ${COLORS.border}`,
                borderRadius: 6, color: COLORS.muted, padding: "3px 10px",
                fontSize: 11, fontFamily: "JetBrains Mono, monospace", cursor: "pointer",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = COLORS.teal; e.currentTarget.style.color = COLORS.teal; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = COLORS.border; e.currentTarget.style.color = COLORS.muted; }}
            >
              ↺ Actualiser
            </button>
          </div>
          <p style={{ fontSize: 13, color: "var(--text)", lineHeight: 1.7, margin: 0 }}>
            {data.resume}
          </p>
          {data.prevision_commentaire && (
            <p style={{
              fontSize: 12, color: COLORS.muted, lineHeight: 1.6,
              margin: "8px 0 0", fontStyle: "italic",
            }}>
              📅 {data.prevision_commentaire}
            </p>
          )}
        </div>
      </div>

      {/* Insights dynamiques */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 20 }}>
        {data.insights.map((ins, i) => (
          <InsightCard key={i} ins={ins} delay={i * 60} />
        ))}
      </div>

      {/* Recommandations par population */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12,
      }}>
        {[
          { key: "grand_public",   label: "Grand public",      icon: "👥", color: COLORS.indigo },
          { key: "vulnerables",    label: "Populations vulnérables", icon: "🏥", color: COLORS.coral },
          { key: "activites_ext",  label: "Activités extérieures", icon: "🌿", color: COLORS.teal },
        ].map(({ key, label, icon, color }, ci) => {
          const conseils = data.recommandations_population[key as keyof typeof data.recommandations_population];
          return (
            <div
              key={key}
              className="fade-up"
              style={{
                animationDelay: `${ci * 80}ms`,
                background: "var(--surface)", border: `1px solid ${COLORS.border}`,
                borderTop: `3px solid ${color}`, borderRadius: "0 0 10px 10px", padding: "14px 16px",
              }}
            >
              <div style={{
                display: "flex", alignItems: "center", gap: 6, marginBottom: 10,
              }}>
                <span style={{ fontSize: 14 }}>{icon}</span>
                <span style={{
                  fontSize: 10, fontWeight: 700, color,
                  fontFamily: "JetBrains Mono, monospace",
                  textTransform: "uppercase", letterSpacing: "0.1em",
                }}>
                  {label}
                </span>
              </div>
              <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 7 }}>
                {conseils.map((c, i) => (
                  <li key={i} style={{ display: "flex", gap: 7, alignItems: "flex-start" }}>
                    <span style={{ color, fontSize: 10, marginTop: 3, flexShrink: 0 }}>◆</span>
                    <span style={{ fontSize: 11, color: COLORS.muted, lineHeight: 1.55, fontFamily: "Outfit, sans-serif" }}>
                      {c}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}