interface Props {
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
  delay?: number;
}

export default function KPICard({ title, value, subtitle, color = "var(--teal)", delay = 0 }: Props) {
  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderBottom: `3px solid ${color}`,
        borderRadius: 12,
        padding: "18px 20px",
        minWidth: 0,
      }}
    >
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          color: "var(--muted)",
          fontFamily: "JetBrains Mono, monospace",
          marginBottom: 8,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 26,
          fontWeight: 800,
          fontFamily: "Syne, sans-serif",
          color: "#E2EAF8",
          lineHeight: 1.1,
          marginBottom: 4,
          letterSpacing: "-0.02em",
        }}
      >
        {value}
      </div>
      {subtitle && (
        <div
          style={{
            fontSize: 11,
            color: "var(--muted)",
            fontFamily: "Outfit, sans-serif",
            lineHeight: 1.4,
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
}