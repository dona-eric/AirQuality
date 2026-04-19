interface Props {
  children: React.ReactNode;
}

export default function SectionTitle({ children }: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        margin: "36px 0 18px",
      }}
    >
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--muted)",
          fontFamily: "JetBrains Mono, monospace",
          whiteSpace: "nowrap",
        }}
      >
        {children}
      </span>
    </div>
  );
}