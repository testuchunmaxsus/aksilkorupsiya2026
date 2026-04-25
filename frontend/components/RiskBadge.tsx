// Risk darajasi belgilarini ko'rsatuvchi 2 ta komponent:
//   <RiskBadge>  — kichik pill (jadval ichida, ro'yxatda)
//   <RiskGauge>  — katta gauge bar (lot detail sahifasida)
type Props = { score: number; level: string; size?: "sm" | "md" | "lg" };

// Daraja → o'zbekcha sarlavha
const labels = {
  high: "YUQORI XAVF",
  medium: "O'RTA XAVF",
  low: "OZ XAVF",
} as const;

// Pill ko'rinishidagi badge — score + daraja matni + rangli nuqta
export function RiskBadge({ score, level, size = "sm" }: Props) {
  const map = {
    high: { color: "var(--red)", bg: "var(--red-soft)" },
    medium: { color: "var(--amber)", bg: "var(--amber-soft)" },
    low: { color: "var(--emerald)", bg: "var(--emerald-soft)" },
  } as const;
  const m = map[level as keyof typeof map] || map.low;
  const fontSize = size === "lg" ? 12 : size === "md" ? 11 : 10.5;
  return (
    <span
      className="inline-flex items-center gap-1.5 mono font-semibold rounded-md px-2 py-1"
      style={{
        fontSize: `${fontSize}px`,
        letterSpacing: "0.08em",
        background: m.bg,
        color: m.color,
      }}
    >
      <span className="inline-block h-2 w-2 rounded-full" style={{ background: m.color }} />
      <span>{labels[level as keyof typeof labels] || level}</span>
      <span className="opacity-60">·</span>
      <span className="font-bold">{Math.round(score)}</span>
    </span>
  );
}

// Katta gauge — lot detail sahifasi yuqorisida ko'rinadi.
// Risk score'ni 0-100 oraliq bar bilan + tick mark'lar (40, 70 chegaralari).
export function RiskGauge({ score, level }: { score: number; level: string }) {
  const map = {
    high: "var(--red)",
    medium: "var(--amber)",
    low: "var(--emerald)",
  } as const;
  const color = map[level as keyof typeof map] || map.low;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="kicker">RISK SCORE</span>
        <span className="text-3xl font-bold tabnum" style={{ color }}>
          {Math.round(score)}
          <span className="text-[var(--fg-dim)] text-base font-medium">/100</span>
        </span>
      </div>
      <div className="relative h-2.5 w-full overflow-hidden bg-[var(--bg-soft)] rounded-full">
        <div
          className="absolute inset-y-0 left-0 transition-all rounded-full"
          style={{ width: `${Math.min(100, score)}%`, background: color }}
        />
        <div className="absolute inset-y-0" style={{ left: "40%", width: "1px", background: "rgba(15,23,42,0.15)" }} />
        <div className="absolute inset-y-0" style={{ left: "70%", width: "1px", background: "rgba(15,23,42,0.15)" }} />
      </div>
      <div className="flex justify-between mt-1.5 text-[10px] mono text-[var(--fg-dim)]">
        <span>0</span>
        <span>40</span>
        <span>70</span>
        <span>100</span>
      </div>
    </div>
  );
}
