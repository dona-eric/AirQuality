"use client";
import { COLORS, CORR_SHORT, POLL_COLS } from "@/lib/constants";

interface Props {
  matrix: number[][];
  labels?: string[];
}

function colorFromCorr(v: number): string {
  // -1 → blue, 0 → dark surface, +1 → teal/coral
  if (v > 0) {
    const t = v;
    const r = Math.round(251 * t + 14 * (1 - t));
    const g = Math.round(146 * t + 20 * (1 - t));
    const b = Math.round(60  * t + 36 * (1 - t));
    return `rgb(${r},${g},${b})`;
  } else {
    const t = -v;
    const r = Math.round(99  * t + 14 * (1 - t));
    const g = Math.round(102 * t + 20 * (1 - t));
    const b = Math.round(241 * t + 36 * (1 - t));
    return `rgb(${r},${g},${b})`;
  }
}

export default function CorrelationHeatmap({ matrix, labels }: Props) {
  const cols = POLL_COLS.slice(0, matrix.length);
  const short = labels ?? cols.map((c) => CORR_SHORT[c] ?? c);
  const n = short.length;

  const CELL = 42;
  const LABEL_W = 46;
  const LABEL_H = 46;
  const W = LABEL_W + n * CELL;
  const H = LABEL_H + n * CELL;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg width={W} height={H} style={{ display: "block" }}>
        {/* Column labels */}
        {short.map((lbl, j) => (
          <text
            key={`col-${j}`}
            x={LABEL_W + j * CELL + CELL / 2}
            y={LABEL_H - 6}
            textAnchor="middle"
            fontSize={9}
            fill={COLORS.muted}
            fontFamily="JetBrains Mono, monospace"
          >
            {lbl}
          </text>
        ))}
        {/* Row labels */}
        {short.map((lbl, i) => (
          <text
            key={`row-${i}`}
            x={LABEL_W - 5}
            y={LABEL_H + i * CELL + CELL / 2 + 4}
            textAnchor="end"
            fontSize={9}
            fill={COLORS.muted}
            fontFamily="JetBrains Mono, monospace"
          >
            {lbl}
          </text>
        ))}
        {/* Cells */}
        {matrix.map((row, i) =>
          row.map((val, j) => {
            const x = LABEL_W + j * CELL;
            const y = LABEL_H + i * CELL;
            const bg = colorFromCorr(val);
            const textColor = Math.abs(val) > 0.5 ? "#fff" : COLORS.muted;
            return (
              <g key={`${i}-${j}`}>
                <rect
                  x={x + 1} y={y + 1}
                  width={CELL - 2} height={CELL - 2}
                  fill={bg}
                  rx={4}
                  opacity={0.85}
                />
                <text
                  x={x + CELL / 2}
                  y={y + CELL / 2 + 4}
                  textAnchor="middle"
                  fontSize={9}
                  fill={textColor}
                  fontFamily="JetBrains Mono, monospace"
                  fontWeight={600}
                >
                  {val.toFixed(2)}
                </text>
              </g>
            );
          })
        )}
      </svg>
      {/* Legend bar */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10, paddingLeft: LABEL_W }}>
        <span style={{ fontSize: 10, color: COLORS.indigo, fontFamily: "JetBrains Mono, monospace" }}>−1</span>
        <div style={{
          flex: 1, height: 6, borderRadius: 3, maxWidth: 200,
          background: "linear-gradient(90deg, #6366F1, #0E1420, #FB923C)",
        }} />
        <span style={{ fontSize: 10, color: COLORS.coral, fontFamily: "JetBrains Mono, monospace" }}>+1</span>
      </div>
    </div>
  );
}