"use client";
import { useEffect, useRef } from "react";
import type { AIRecommendations, AIInsight } from "@/lib/useiainsights";
import { COLORS } from "@/lib/constants";

/* ── Couleurs de niveau ── */
const NIVEAU_COLOR: Record<string, string> = {
  Bon:            COLORS.teal,
  Modéré:         COLORS.amber,
  Mauvais:        COLORS.coral,
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

/* ── Jauge SVG ── */
function RiskGauge({ score }: { score: number }) {
  const pct   = score / 100;
  const r     = 44;
  const cx = 56, cy = 56;
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
      <path d={arcPath(start, start + sweep)} fill="none" stroke="var(--surface2)" strokeWidth={10} strokeLinecap="round" />
      <path d={arcPath(start, ang)}           fill="none" stroke={color}            strokeWidth={10} strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={toXY(ang).x} y2={toXY(ang).y}
        stroke={color} strokeWidth={2.5} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={4} fill={color} />
      <text x={cx} y={cy + 18} textAnchor="middle" fontSize={22} fontWeight={800}
        fill={color} fontFamily="Syne, sans-serif">{score}</text>
      <text x={cx} y={cy + 31} textAnchor="middle" fontSize={10}
        fill="var(--muted)" fontFamily="JetBrains Mono, monospace">/ 100</text>
    </svg>
  );
}

/* ── Curseur streaming ── */
function StreamCursor() {
  return (
    <span style={{
      display: "inline-block", width: 2, height: 15,
      background: COLORS.teal, marginLeft: 4, verticalAlign: "middle",
      animation: "pulse-dot 0.8s ease-in-out infinite",
    }} />
  );
}

/* ── Carte insight individuelle ── */
function InsightCard({ ins, delay }: { ins: AIInsight; delay: number }) {
  const pc = PRIO_COLOR[ins.priorite];
  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        background: "var(--surface)",
        border: `1px solid var(--border)`,
        borderLeft: `4px solid ${pc}`,
        borderRadius: "0 12px 12px 0",
        padding: "16px 20px",
      }}
    >
      {/* Badge catégorie + priorité */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 16 }}>{CAT_ICON[ins.categorie] ?? "●"}</span>
        <span style={{
          fontSize: 11,
          fontFamily: "JetBrains Mono, monospace",
          fontWeight: 700,
          color: pc,
          textTransform: "uppercase",
          letterSpacing: "0.10em",
          background: `${pc}12`,
          padding: "2px 8px",
          borderRadius: 20,
          border: `1px solid ${pc}30`,
        }}>
          {ins.categorie} · {ins.priorite}
        </span>
      </div>

      {/* Titre */}
      <div style={{
        fontFamily: "Syne, sans-serif",
        fontWeight: 700,
        fontSize: 15,           /* était 13 */
        color: "var(--text)",
        marginBottom: 8,
        lineHeight: 1.35,
      }}>
        {ins.titre}
      </div>

      {/* Corps — lisibilité améliorée */}
      <p style={{
        fontSize: 13,           /* était 12 */
        fontFamily: "Outfit, sans-serif",
        fontWeight: 400,
        color: "var(--text)",   /* était COLORS.muted — trop pâle */
        lineHeight: 1.75,
        margin: "0 0 12px",
        opacity: 0.85,          /* légère atténuation sans perdre la lisibilité */
      }}>
        {ins.texte}
      </p>

      {/* Action recommandée */}
      <div style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 8,
        background: `${pc}0D`,
        border: `1px solid ${pc}30`,
        borderRadius: 8,
        padding: "9px 12px",
      }}>
        <span style={{ color: pc, fontSize: 13, lineHeight: 1, marginTop: 2, flexShrink: 0 }}>→</span>
        <span style={{
          fontSize: 13,         /* était 11 */
          fontFamily: "Outfit, sans-serif",
          fontWeight: 500,      /* était 400 */
          color: "var(--text)",
          lineHeight: 1.6,
        }}>
          {ins.action}
        </span>
      </div>
    </div>
  );
}

/* ── Props ── */
interface Props {
  data:      AIRecommendations | null;
  loading:   boolean;
  streaming: boolean;
  rawText:   string;
  error:     string | null;
  onRefresh: () => void;
}

export default function AIInsightsPanel({ data, loading, streaming, rawText, error, onRefresh }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (streaming && scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [rawText, streaming]);

  /* ── Loading / streaming ── */
  if (loading || (streaming && !data)) {
    return (
      <div style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: 12, padding: 24,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
          <div style={{ width: 112, height: 90, background: "var(--surface2)", borderRadius: 8, flexShrink: 0 }} />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
            {[60, 90, 75].map((w, i) => (
              <div key={i} className="skeleton" style={{ height: 14, width: `${w}%` }} />
            ))}
          </div>
        </div>
        {rawText ? (
          <div
            ref={scrollRef}
            style={{
              background: "var(--surface2)",
              border: "1px solid var(--border)",
              borderRadius: 8, padding: "14px 18px",
              maxHeight: 180, overflowY: "auto",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: 12,             /* légèrement plus grand */
              fontWeight: 400,
              color: "var(--text)",     /* CSS var, adaptatif */
              lineHeight: 1.7,
              whiteSpace: "pre-wrap", wordBreak: "break-word",
            }}
          >
            {rawText}
            <StreamCursor />
          </div>
        ) : (
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            color: "var(--muted)",
            fontFamily: "JetBrains Mono, monospace", fontSize: 13,
          }}>
            <div className="live-dot" />
            Analyse des données en cours par l'IA…
          </div>
        )}
      </div>
    );
  }

  /* ── Erreur ── */
  if (error) {
    return (
      <div style={{
        background: `${COLORS.danger}08`,
        border: `1px solid ${COLORS.danger}`,
        borderRadius: 12, padding: 20,
      }}>
        <div style={{
          fontSize: 13, fontWeight: 500,
          color: COLORS.danger,
          fontFamily: "Outfit, sans-serif",
          marginBottom: 12, lineHeight: 1.5,
        }}>
          ⚠ Erreur lors de l'analyse IA : {error}
        </div>
        <button onClick={onRefresh} style={{
          background: `${COLORS.danger}12`,
          border: `1px solid ${COLORS.danger}`,
          borderRadius: 8, color: COLORS.danger,
          padding: "7px 16px", fontSize: 13,
          fontFamily: "Outfit, sans-serif",
          fontWeight: 600, cursor: "pointer",
        }}>
          Réessayer
        </button>
      </div>
    );
  }

  /* ── Vide ── */
  if (!data) {
    return (
      <div style={{
        background: "var(--surface)",
        border: "1px dashed var(--border)",
        borderRadius: 12, padding: 40,
        textAlign: "center",
      }}>
        <div style={{ fontSize: 36, marginBottom: 14 }}>🤖</div>
        <div style={{
          fontSize: 14, fontFamily: "Outfit, sans-serif",
          fontWeight: 500, color: "var(--muted)", marginBottom: 18,
        }}>
          Aucune analyse générée. Cliquez pour lancer l'analyse IA.
        </div>
        <button onClick={onRefresh} style={{
          background: `${COLORS.teal}15`,
          border: `1px solid ${COLORS.teal}`,
          borderRadius: 10, color: COLORS.teal,
          padding: "10px 24px",
          fontSize: 14, fontFamily: "Outfit, sans-serif",
          fontWeight: 600, cursor: "pointer",
        }}>
          Lancer l'analyse →
        </button>
      </div>
    );
  }

  /* ── Données disponibles ── */
  const niveauColor = NIVEAU_COLOR[data.niveau_global] ?? "var(--muted)";

  return (
    <div>
      {/* Alerte urgente */}
      {data.alerte && (
        <div className="fade-up" style={{
          background: `${COLORS.danger}08`,
          border: `1px solid ${COLORS.danger}`,
          borderLeft: `4px solid ${COLORS.danger}`,
          borderRadius: "0 12px 12px 0",
          padding: "14px 20px", marginBottom: 16,
          display: "flex", alignItems: "flex-start", gap: 12,
        }}>
          <span style={{ fontSize: 20, flexShrink: 0 }}>🚨</span>
          <span style={{
            fontSize: 14,             /* était 13 */
            fontFamily: "Outfit, sans-serif",
            fontWeight: 500,          /* était 400 */
            color: COLORS.danger,
            lineHeight: 1.6,
          }}>
            {data.alerte}
          </span>
        </div>
      )}

      {/* En-tête : jauge + résumé */}
      <div className="fade-up" style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 14, padding: "22px 26px",
        marginBottom: 14,
        display: "grid",
        gridTemplateColumns: "auto 1fr",
        gap: 28, alignItems: "center",
        boxShadow: "var(--shadow-sm)",
      }}>
        {/* Jauge */}
        <div style={{ textAlign: "center" }}>
          <RiskGauge score={data.score_risque} />
          <div style={{
            fontSize: 11, fontFamily: "JetBrains Mono, monospace",
            fontWeight: 600,
            color: "var(--muted)", marginTop: 4,
            textTransform: "uppercase", letterSpacing: "0.08em",
          }}>
            Score de risque
          </div>
        </div>

        {/* Résumé */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <span style={{
              fontSize: 11, fontWeight: 700,
              fontFamily: "JetBrains Mono, monospace",
              color: niveauColor,
              textTransform: "uppercase", letterSpacing: "0.12em",
              background: `${niveauColor}15`,
              padding: "4px 12px", borderRadius: 20,
              border: `1px solid ${niveauColor}40`,
            }}>
              {data.niveau_global}
            </span>
            <button
              onClick={onRefresh}
              style={{
                background: "transparent",
                border: "1px solid var(--border)",
                borderRadius: 6, color: "var(--muted)",
                padding: "3px 10px", fontSize: 11,
                fontFamily: "JetBrains Mono, monospace",
                cursor: "pointer", transition: "all 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = COLORS.teal;
                e.currentTarget.style.color = COLORS.teal;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.color = "var(--muted)";
              }}
            >
              ↺ Actualiser
            </button>
          </div>

          {/* Résumé — le texte principal IA */}
          <p style={{
            fontSize: 14,             /* était 13 */
            fontFamily: "Outfit, sans-serif",
            fontWeight: 400,
            color: "var(--text)",
            lineHeight: 1.80,         /* aération pour la lecture */
            margin: 0,
          }}>
            {data.resume}
          </p>

          {data.prevision_commentaire && (
            <p style={{
              fontSize: 13,           /* était 12 */
              fontFamily: "Outfit, sans-serif",
              fontWeight: 400,
              color: "var(--muted)",
              lineHeight: 1.65,
              margin: "10px 0 0",
              fontStyle: "italic",
            }}>
              📅 {data.prevision_commentaire}
            </p>
          )}
        </div>
      </div>

      {/* Insights */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 22 }}>
        {data.insights.map((ins, i) => (
          <InsightCard key={i} ins={ins} delay={i * 60} />
        ))}
      </div>

      {/* Recommandations par population */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
        {[
          { key: "grand_public",  label: "Grand public",           icon: "👥", color: COLORS.indigo },
          { key: "vulnerables",   label: "Populations vulnérables", icon: "🏥", color: COLORS.coral  },
          { key: "activites_ext", label: "Activités extérieures",  icon: "🌿", color: COLORS.teal   },
        ].map(({ key, label, icon, color }, ci) => {
          const conseils = data.recommandations_population[key as keyof typeof data.recommandations_population];
          return (
            <div
              key={key}
              className="fade-up"
              style={{
                animationDelay: `${ci * 80}ms`,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderTop: `3px solid ${color}`,
                borderRadius: "0 0 12px 12px",
                padding: "16px 18px",
                minWidth: 0,
              }}
            >
              {/* En-tête */}
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
                <span style={{ fontSize: 16 }}>{icon}</span>
                <span style={{
                  fontSize: 11, fontWeight: 700, color,
                  fontFamily: "JetBrains Mono, monospace",
                  textTransform: "uppercase", letterSpacing: "0.10em",
                }}>
                  {label}
                </span>
              </div>

              {/* Conseils */}
              <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 9 }}>
                {conseils.map((c, i) => (
                  <li key={i} style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
                    <span style={{ color, fontSize: 11, marginTop: 4, flexShrink: 0 }}>◆</span>
                    <span style={{
                      fontSize: 13,       /* était 11 — illisible */
                      fontFamily: "Outfit, sans-serif",
                      fontWeight: 400,
                      color: "var(--text)",   /* était COLORS.muted */
                      lineHeight: 1.65,
                    }}>
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