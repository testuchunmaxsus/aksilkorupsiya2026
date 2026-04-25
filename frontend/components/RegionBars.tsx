"use client";
import { REGION_NAMES } from "@/lib/api";

type Row = { region: string; count: number; high?: number };

export function RegionBars({
  rows,
  highRows,
}: {
  rows: { region: string; count: number }[];
  highRows: { region: string; high_count: number }[];
}) {
  const highMap = Object.fromEntries(
    highRows.map((r) => [r.region, r.high_count])
  );
  const merged: Row[] = rows
    .map((r) => ({ ...r, high: highMap[r.region] || 0 }))
    .sort((a, b) => b.count - a.count);

  const max = Math.max(...merged.map((r) => r.count), 1);

  return (
    <div className="card overflow-hidden">
      <div className="border-b border-[var(--line)] px-5 py-4 bg-[var(--bg-soft)]">
        <div className="kicker">HUDUDLAR · REGION BREAKDOWN</div>
        <div className="font-bold text-lg text-[var(--fg)]">
          Lot taqsimoti
        </div>
      </div>
      <div className="divide-y divide-[var(--line-soft)]">
        {merged.map((r) => {
          const w = (r.count / max) * 100;
          const hw = ((r.high || 0) / max) * 100;
          return (
            <div key={r.region} className="grid grid-cols-12 gap-3 items-center px-5 py-3">
              <div className="col-span-3 text-sm text-[var(--fg)] font-medium">
                {REGION_NAMES[r.region] || r.region}
              </div>
              <div className="col-span-7 relative h-2.5 bg-[var(--bg-soft)] rounded-full overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-[var(--primary-mid)] rounded-full"
                  style={{ width: `${w}%` }}
                />
                {r.high ? (
                  <div
                    className="absolute inset-y-0 left-0 bg-[var(--red)] rounded-full"
                    style={{ width: `${hw}%` }}
                  />
                ) : null}
              </div>
              <div className="col-span-2 mono text-xs text-right">
                <span className="text-[var(--fg)] font-semibold">{r.count}</span>
                {r.high ? (
                  <span className="text-[var(--red)]"> · {r.high} 🚩</span>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
