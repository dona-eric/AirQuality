interface Props {
  title?: string;
  caption?: string;
  children: React.ReactNode;
  delay?: number;
}

export default function ChartCard({ title, caption, children, delay = 0 }: Props) {
  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "18px",
        minWidth: 0,
      }}
    >
      {title && (
        <div
          style={{
            fontFamily: "Syne, sans-serif",
            fontWeight: 700,
            fontSize: 13,
            color: "var(--text)",
            marginBottom: caption ? 2 : 12,
          }}
        >
          {title}
        </div>
      )}
      {caption && (
        <div
          style={{
            fontSize: 11,
            color: "var(--muted)",
            fontFamily: "Outfit, sans-serif",
            marginBottom: 12,
          }}
        >
          {caption}
        </div>
      )}
      {children}
    </div>
  );
}