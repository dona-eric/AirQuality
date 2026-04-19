"use client";
import { useState } from "react";
import { NAV_ITEMS } from "@/lib/constants";
import type { PageId } from "@/lib/types";

interface Props {
  active: PageId;
  onChange: (id: PageId) => void;
  apiUrl: string;
  onApiChange: (url: string) => void;
  onRefresh: () => void;
}

export default function Sidebar({ active, onChange, apiUrl, onApiChange, onRefresh }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <aside
      style={{
        width: 228,
        minHeight: "100vh",
        background: "linear-gradient(180deg, #0e1624 0%, #0d1427 100%)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        padding: "24px 0 20px",
        position: "sticky",
        top: 0,
        flexShrink: 0,
        overflowY: "auto",
      }}
    >
      {/* Logo */}
      <div style={{ padding: "0 20px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 24, lineHeight: 1 }}>🌬️</span>
          <div>
            <div style={{ fontFamily: "Syne, sans-serif", fontWeight: 800, fontSize: 17, color: "var(--teal)", letterSpacing: "-0.03em", lineHeight: 1.1 }}>
              <span>AQI Cotonou</span>
            </div>
            <div style={{ fontSize: 10, color: "var(--muted)", fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.05em", marginTop: 2 }}>
              Surveillance & IA
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "0 10px" }}>
        <div style={{ fontSize: 9, fontFamily: "JetBrains Mono, monospace", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.14em", padding: "0 10px 8px", opacity: 0.6 }}>
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
                marginBottom: 3,
                borderRadius: 8,
                border: "none",
                borderLeft: isActive ? "3px solid var(--teal)" : "3px solid transparent",
                background: isActive ? "rgba(0,229,180,0.08)" : isHovered ? "rgba(200,212,232,0.04)" : "transparent",
                color: isActive ? "var(--teal)" : isHovered ? "var(--text)" : "var(--muted)",
                fontSize: 13,
                fontFamily: "Outfit, sans-serif",
                fontWeight: isActive ? 600 : 400,
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s ease",
              }}
            >
              <span style={{ fontSize: 15, opacity: isActive ? 1 : isHovered ? 0.85 : 0.5, transition: "opacity 0.15s", flexShrink: 0 }}>
                {item.icon}
              </span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {isActive && (
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--teal)", flexShrink: 0 }} />
              )}
            </button>
          );
        })}
      </nav>

      {/* API settings */}
      <div style={{ padding: "0 14px" }}>
        <div style={{ fontSize: 9, color: "var(--muted)", fontFamily: "JetBrains Mono, monospace", textTransform: "uppercase", letterSpacing: "0.14em", marginBottom: 8, opacity: 0.7 }}>
          API Endpoint
        </div>
        <input
          value={apiUrl}
          onChange={(e) => onApiChange(e.target.value)}
          spellCheck={false}
          style={{
            width: "100%",
            background: "#0A0F1C",
            border: "1px solid var(--border)",
            borderRadius: 6,
            color: "var(--text)",
            padding: "7px 9px",
            fontSize: 11,
            fontFamily: "JetBrains Mono, monospace",
            outline: "none",
            marginBottom: 8,
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--teal)")}
          onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
        />
        <button
          onClick={onRefresh}
          style={{
            width: "100%",
            background: "rgba(0,229,180,0.07)",
            border: "1px solid var(--teal)",
            borderRadius: 6,
            color: "var(--teal)",
            padding: "8px 0",
            fontSize: 12,
            fontFamily: "JetBrains Mono, monospace",
            fontWeight: 600,
            cursor: "pointer",
            letterSpacing: "0.04em",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "var(--teal)"; e.currentTarget.style.color = "#080C14"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(0,229,180,0.07)"; e.currentTarget.style.color = "var(--teal)"; }}
        >
          ↺ Rafraîchir
        </button>
      </div>
    </aside>
  );
}