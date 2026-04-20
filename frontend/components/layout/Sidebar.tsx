"use client";
import { useState } from "react";
import { NAV_ITEMS } from "@/lib/constants";
import type { PageId } from "@/lib/types";
import type { Theme } from "@/lib/useTheme"; // ajustez le chemin selon votre structure

interface Props {
  active: PageId;
  onChange: (id: PageId) => void;
  apiUrl: string;
  onApiChange: (url: string) => void;
  onRefresh: () => void;
  theme: Theme;
  onThemeToggle: () => void;
}

export default function Sidebar({
  active, onChange,
  apiUrl, onApiChange,
  onRefresh,
  theme, onThemeToggle,
}: Props) {
  const [hovered, setHovered] = useState<string | null>(null);
  const isDark = theme === "dark";

  /* ── Palette sidebar (toujours sombre, identité visuelle fixe) ── */
  const S = {
    bg:       "linear-gradient(180deg, #141E35 0%, #111929 100%)",
    border:   "#1E2E4A",
    muted:    "#7A8BA8",
    text:     "#C8D4E8",
    teal:     "#00C49A",
    active:   "rgba(0,196,154,0.10)",
    hover:    "rgba(200,212,232,0.05)",
    input:    "#0A1120",
    btnBg:    "rgba(0,196,154,0.08)",
  };

  return (
    <aside
      style={{
        width: 234,
        minHeight: "100vh",
        background: S.bg,
        borderRight: `1px solid ${S.border}`,
        display: "flex",
        flexDirection: "column",
        padding: "24px 0 20px",
        position: "sticky",
        top: 0,
        flexShrink: 0,
        overflowY: "auto",
        /* Pas de transition sur le sidebar — il reste sombre toujours */
        transition: "none",
      }}
    >
      {/* ── Logo ── */}
      <div style={{ padding: "0 20px 22px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 24, lineHeight: 1 }}>🌬️</span>
          <div>
            <div style={{
              fontFamily: "Syne, sans-serif", fontWeight: 800,
              fontSize: 16, color: S.teal,
              letterSpacing: "-0.03em", lineHeight: 1.1,
            }}>
              AQI Cotonou
            </div>
            <div style={{
              fontSize: 9.5, color: S.muted,
              fontFamily: "JetBrains Mono, monospace",
              letterSpacing: "0.06em", marginTop: 2,
            }}>
              Surveillance & IA
            </div>
          </div>
        </div>
      </div>

      {/* ── Nav ── */}
      <nav style={{ flex: 1, padding: "0 10px" }}>
        <div style={{
          fontSize: 9, fontFamily: "JetBrains Mono, monospace",
          color: S.muted, textTransform: "uppercase",
          letterSpacing: "0.15em", padding: "0 10px 8px", opacity: 0.55,
        }}>
          Menu
        </div>

        {NAV_ITEMS.map((item) => {
          const isActive  = active === item.id;
          const isHovered = hovered === item.id && !isActive;
          return (
            <button
              key={item.id}
              onClick={() => onChange(item.id as PageId)}
              onMouseEnter={() => setHovered(item.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "9px 12px",
                marginBottom: 2,
                borderRadius: 8,
                border: "none",
                borderLeft: isActive ? `3px solid ${S.teal}` : "3px solid transparent",
                background: isActive ? S.active : isHovered ? S.hover : "transparent",
                color: isActive ? S.teal : isHovered ? S.text : S.muted,
                fontSize: 13,
                fontFamily: "Outfit, sans-serif",
                fontWeight: isActive ? 600 : 400,
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s ease",
              }}
            >
              <span style={{
                fontSize: 15,
                opacity: isActive ? 1 : isHovered ? 0.85 : 0.45,
                transition: "opacity 0.15s",
                flexShrink: 0,
              }}>
                {item.icon}
              </span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {isActive && (
                <span style={{
                  width: 5, height: 5, borderRadius: "50%",
                  background: S.teal, flexShrink: 0,
                }} />
              )}
            </button>
          );
        })}
      </nav>

      {/* ── Séparateur ── */}
      <div style={{ height: 1, background: S.border, margin: "12px 14px" }} />

      {/* ── Bascule thème ── */}
      <div style={{ padding: "0 14px 10px" }}>
        <div style={{
          fontSize: 9, color: S.muted,
          fontFamily: "JetBrains Mono, monospace",
          textTransform: "uppercase", letterSpacing: "0.14em",
          marginBottom: 8, opacity: 0.6,
        }}>
          Apparence
        </div>
        <button
          onClick={onThemeToggle}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: S.input,
            border: `1px solid ${S.border}`,
            borderRadius: 8,
            padding: "8px 12px",
            color: S.text,
            fontSize: 12,
            fontFamily: "Outfit, sans-serif",
            cursor: "pointer",
            transition: "border-color 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = S.teal)}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = S.border)}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <span style={{ fontSize: 14 }}>{isDark ? "🌙" : "☀️"}</span>
            <span>{isDark ? "Mode sombre" : "Mode clair"}</span>
          </span>

          {/* Toggle pill */}
          <span style={{
            display: "inline-flex",
            width: 34, height: 18,
            background: isDark ? S.teal : "#334155",
            borderRadius: 9,
            position: "relative",
            transition: "background 0.2s ease",
            flexShrink: 0,
          }}>
            <span style={{
              position: "absolute",
              top: 3, left: isDark ? 18 : 3,
              width: 12, height: 12,
              borderRadius: "50%",
              background: "#fff",
              transition: "left 0.2s ease",
            }} />
          </span>
        </button>
      </div>

      {/* ── API Endpoint ── */}
      <div style={{ padding: "0 14px" }}>
        <div style={{
          fontSize: 9, color: S.muted,
          fontFamily: "JetBrains Mono, monospace",
          textTransform: "uppercase", letterSpacing: "0.14em",
          marginBottom: 8, opacity: 0.6,
        }}>
          API Endpoint
        </div>
        <input
          value={apiUrl}
          onChange={(e) => onApiChange(e.target.value)}
          spellCheck={false}
          style={{
            width: "100%",
            background: S.input,
            border: `1px solid ${S.border}`,
            borderRadius: 6,
            color: S.text,
            padding: "7px 9px",
            fontSize: 10.5,
            fontFamily: "JetBrains Mono, monospace",
            outline: "none",
            marginBottom: 8,
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = S.teal)}
          onBlur={(e)  => (e.currentTarget.style.borderColor = S.border)}
        />
        <button
          onClick={onRefresh}
          style={{
            width: "100%",
            background: S.btnBg,
            border: `1px solid ${S.teal}`,
            borderRadius: 6,
            color: S.teal,
            padding: "8px 0",
            fontSize: 12,
            fontFamily: "JetBrains Mono, monospace",
            fontWeight: 600,
            cursor: "pointer",
            letterSpacing: "0.04em",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = S.teal;
            e.currentTarget.style.color = "#080C14";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = S.btnBg;
            e.currentTarget.style.color = S.teal;
          }}
        >
          ↺ Rafraîchir
        </button>
      </div>
    </aside>
  );
}