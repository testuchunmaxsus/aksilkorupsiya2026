import { CATEGORY_LABEL, type Categories } from "@/lib/api";

const CATEGORY_COLOR: Record<string, string> = {
  A: "#f97316",
  B: "#a855f7",
  C: "#dc2626",
  D: "#ca8a04",
  E: "#0891b2",
};

export function CategoryBars({
  categories,
  total,
}: {
  categories: Categories | null;
  total: number;
}) {
  if (!categories) return null;
  const order: (keyof Categories)[] = ["A", "B", "C", "D", "E"];
  const max = Math.max(100, ...order.map((k) => categories[k]));
  const activeCount = order.filter((k) => categories[k] > 0).length;

  return (
    <div className="card overflow-hidden">
      <div className="border-b border-[var(--line)] px-5 py-3 bg-[var(--bg-soft)] flex items-center justify-between">
        <div>
          <div className="kicker">OECD/OCP TOIFALAR</div>
          <div className="font-bold text-[var(--fg)]">
            {activeCount}/5 toifada signal
          </div>
        </div>
        <div
          className="text-2xl font-bold tabnum"
          style={{
            color:
              total >= 70
                ? "var(--red)"
                : total >= 40
                ? "var(--amber)"
                : "var(--emerald)",
          }}
        >
          {Math.round(total)}
        </div>
      </div>
      <div className="px-5 py-4 space-y-3">
        {order.map((key) => {
          const val = categories[key] || 0;
          const pct = (val / max) * 100;
          const meta = CATEGORY_LABEL[key];
          const color = CATEGORY_COLOR[key];
          return (
            <div key={key}>
              <div className="flex items-baseline justify-between mb-1.5">
                <div className="flex items-baseline gap-2">
                  <span
                    className="mono text-xs font-bold"
                    style={{ color }}
                  >
                    {key}
                  </span>
                  <span className="text-sm text-[var(--fg)]">{meta.name}</span>
                </div>
                <span className="mono tabnum text-xs text-[var(--fg-mute)] font-semibold">
                  {Math.round(val)}
                </span>
              </div>
              <div className="relative h-2 bg-[var(--bg-soft)] rounded-full overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 transition-all rounded-full"
                  style={{
                    width: `${pct}%`,
                    background: val > 0 ? color : "transparent",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="border-t border-[var(--line)] px-5 py-2.5 text-[10px] mono text-[var(--fg-dim)] uppercase tracking-wider leading-relaxed bg-[var(--bg-soft)]">
        OECD Anti-Corruption Outlook + OCP Cardinal standartiga muvofiq
      </div>
    </div>
  );
}
