"use client";

export function ScoreRing({
  score,
  label,
  size = 120,
}: {
  score: number;
  label: string;
  size?: number;
}) {
  const r = (size - 12) / 2;
  const C = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, score));
  const offset = C - (pct / 100) * C;
  const color =
    score >= 80
      ? "var(--success)"
      : score >= 60
        ? "var(--warning)"
        : "var(--danger)";

  return (
    <div style={{ textAlign: "center", display: "inline-block" }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="8"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text
          x={size / 2}
          y={size / 2 - 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill="var(--foreground)"
          fontSize="26"
          fontWeight="bold"
        >
          {score}
        </text>
        <text
          x={size / 2}
          y={size / 2 + 22}
          textAnchor="middle"
          fill="var(--muted)"
          fontSize="11"
        >
          {label}
        </text>
      </svg>
    </div>
  );
}

export function BreakdownBar({
  label,
  value,
  max = 100,
  color,
}: {
  label: string;
  value: number;
  max?: number;
  color?: string;
}) {
  const pct = Math.min(100, (value / max) * 100);
  const barColor =
    color ||
    (pct >= 80
      ? "var(--success)"
      : pct >= 50
        ? "var(--warning)"
        : "var(--danger)");

  return (
    <div className="breakdown-row">
      <span className="breakdown-label">{label}</span>
      <div className="breakdown-track">
        <div
          className="breakdown-fill"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      <span className="breakdown-value">{value}</span>
    </div>
  );
}
