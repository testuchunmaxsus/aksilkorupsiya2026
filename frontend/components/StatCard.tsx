export function StatCard({
  label,
  value,
  hint,
  trend,
  accent = "default",
  icon,
}: {
  label: string;
  value: string | number;
  hint?: string;
  trend?: string;
  accent?: "default" | "danger" | "warn" | "ok";
  icon?: string;
}) {
  const accentMap = {
    default: { bg: "var(--primary-soft)", color: "var(--primary)" },
    danger: { bg: "var(--red-soft)", color: "var(--red)" },
    warn: { bg: "var(--amber-soft)", color: "var(--amber)" },
    ok: { bg: "var(--emerald-soft)", color: "var(--emerald)" },
  }[accent];
  return (
    <div className="card p-5 card-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="kicker">{label}</div>
        {icon && (
          <div
            className="h-9 w-9 rounded-lg inline-flex items-center justify-center"
            style={{ background: accentMap.bg, color: accentMap.color }}
          >
            <span className="text-lg">{icon}</span>
          </div>
        )}
      </div>
      <div
        className="mt-3 text-3xl font-bold tabnum tracking-tight"
        style={{ color: accentMap.color }}
      >
        {value}
      </div>
      {hint && (
        <div className="mt-1.5 text-xs text-[var(--fg-mute)]">{hint}</div>
      )}
      {trend && (
        <div className="mt-2 inline-block kicker text-[10px]">
          {trend}
        </div>
      )}
    </div>
  );
}
