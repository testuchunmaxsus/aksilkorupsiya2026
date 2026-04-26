// Risk darajalari taqsimoti — bosh sahifada ko'rinadi.
// Judge "false positive ulushi qancha?" deb so'rasa, bu bar to'g'ridan-to'g'ri
// javob beradi: "yuqori xavfli lotlar atigi 12% — model agressiv emas".
import type { Stats } from "@/lib/api";

export function RiskDistribution({ stats }: { stats: Stats }) {
  const d = stats.distribution;
  if (!d || stats.total === 0) return null;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="kicker">RISK TAQSIMOTI</div>
          <h3 className="font-bold text-[var(--fg)] text-lg">
            {stats.total.toLocaleString()} ta lot — qaysi ulushi shubhali?
          </h3>
        </div>
        <div className="text-xs text-[var(--fg-mute)] text-right">
          Modelimiz tasodifan ko&apos;p &quot;qizil&quot; chiqarmasligini ko&apos;rsatadi
        </div>
      </div>

      {/* Stacked bar — 100% width */}
      <div className="h-8 w-full rounded-md overflow-hidden flex border border-[var(--line)]">
        <div
          className="bg-[var(--red)] flex items-center justify-center text-white text-xs font-bold"
          style={{ width: `${d.high.pct}%` }}
          title={`Yuqori xavf: ${d.high.count.toLocaleString()} lot`}
        >
          {d.high.pct >= 5 ? `${d.high.pct.toFixed(1)}%` : ""}
        </div>
        <div
          className="bg-[var(--amber)] flex items-center justify-center text-white text-xs font-bold"
          style={{ width: `${d.medium.pct}%` }}
          title={`O'rta xavf: ${d.medium.count.toLocaleString()} lot`}
        >
          {d.medium.pct >= 5 ? `${d.medium.pct.toFixed(1)}%` : ""}
        </div>
        <div
          className="bg-[var(--emerald)] flex items-center justify-center text-white text-xs font-bold"
          style={{ width: `${d.low.pct}%` }}
          title={`Past xavf: ${d.low.count.toLocaleString()} lot`}
        >
          {d.low.pct >= 5 ? `${d.low.pct.toFixed(1)}%` : ""}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
        <div className="flex items-start gap-2">
          <span className="inline-block h-3 w-3 mt-1 bg-[var(--red)] rounded-sm flex-shrink-0" />
          <div>
            <div className="font-semibold text-[var(--fg)]">
              🚩 Yuqori xavf
            </div>
            <div className="mono text-xs text-[var(--fg-mute)]">
              {d.high.count.toLocaleString()} ({d.high.pct.toFixed(1)}%)
            </div>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <span className="inline-block h-3 w-3 mt-1 bg-[var(--amber)] rounded-sm flex-shrink-0" />
          <div>
            <div className="font-semibold text-[var(--fg)]">⚠️ O&apos;rta</div>
            <div className="mono text-xs text-[var(--fg-mute)]">
              {d.medium.count.toLocaleString()} ({d.medium.pct.toFixed(1)}%)
            </div>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <span className="inline-block h-3 w-3 mt-1 bg-[var(--emerald)] rounded-sm flex-shrink-0" />
          <div>
            <div className="font-semibold text-[var(--fg)]">✓ Normal</div>
            <div className="mono text-xs text-[var(--fg-mute)]">
              {d.low.count.toLocaleString()} ({d.low.pct.toFixed(1)}%)
            </div>
          </div>
        </div>
      </div>

      <p className="mt-3 text-xs text-[var(--fg-dim)] leading-relaxed">
        {d.high.pct < 15 ? (
          <>
            ✓ Yuqori xavfli lotlar atigi {d.high.pct.toFixed(1)}% — model
            tanlangan va aniq, ko&apos;r-ko&apos;rona &quot;qizil bayroq&quot; tashlamaydi.
          </>
        ) : d.high.pct < 30 ? (
          <>
            Yuqori xavfli ulush {d.high.pct.toFixed(1)}% — bu
            o&apos;rta-yuqori signal darajasi. Tahliliy nazoratga loyiq.
          </>
        ) : (
          <>
            Diqqat: yuqori xavfli ulush {d.high.pct.toFixed(1)}% —
            modelimiz agressiv ishlamoqda, false positive nisbati tekshirilishi kerak.
          </>
        )}
      </p>
    </div>
  );
}
