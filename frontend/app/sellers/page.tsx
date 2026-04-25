import Link from "next/link";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SellersPage() {
  const data = await api.sellers(50).catch(() => ({ items: [] }));
  const items = data.items;

  const totalLots = items.reduce((s, x) => s + x.total_lots, 0);
  const top3 = items.slice(0, 3).reduce((s, x) => s + x.total_lots, 0);
  const top3pct = totalLots > 0 ? (top3 / totalLots) * 100 : 0;

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker">REYTING · LEADERBOARD</div>
        <h1 className="headline mt-2 text-4xl text-white">
          Sotuvchilar reytingi
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Lotlar soni bo&apos;yicha eng yirik buyurtmachilar (sotuvchilar) ro&apos;yxati.
          Yopiq auksion ulushi va yuqori xavfli lotlar foizi — Chexiya
          <em className="text-zinc-300 not-italic"> zIndex.cz</em> metodologiyasiga muvofiq.
        </p>
        {top3pct > 50 && (
          <div className="mt-4 inline-flex items-center gap-2 rounded border border-red-900/50 bg-red-950/40 px-3 py-1.5 mono text-xs">
            <span className="text-[var(--red)]">●</span>
            <span className="text-zinc-300">
              TOP 3 sotuvchi {top3.toLocaleString()} ta lot ({top3pct.toFixed(1)}%) ni
              nazorat qiladi — <strong className="text-red-300">state capture</strong> belgisi
            </span>
          </div>
        )}
      </header>

      <div className="mt-6 card overflow-hidden">
        <table className="tbl">
          <thead>
            <tr>
              <th>#</th>
              <th>Sotuvchi</th>
              <th>Hudud</th>
              <th className="text-right">Lotlar</th>
              <th className="text-right">Yopiq %</th>
              <th className="text-right">Yuqori xavf %</th>
              <th className="text-right">O&apos;rtacha risk</th>
              <th className="text-right">Qiymat</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s, i) => {
              const isHigh = s.high_risk_pct >= 50;
              return (
                <tr key={s.seller_id}>
                  <td className="mono text-[var(--fg-dim)] tabnum w-8">
                    {String(i + 1).padStart(2, "0")}
                  </td>
                  <td>
                    <Link
                      href={`/seller/${s.seller_id}`}
                      className="block group"
                    >
                      <div className="text-zinc-100 link-u line-clamp-1 max-w-md">
                        {s.seller_name || `Sotuvchi #${s.seller_id}`}
                      </div>
                      <div className="mono text-[10px] text-[var(--fg-dim)]">
                        ID: {s.seller_id}
                      </div>
                    </Link>
                  </td>
                  <td className="text-zinc-300 text-sm whitespace-nowrap">
                    {s.region ? REGION_NAMES[s.region] || s.region : "—"}
                  </td>
                  <td className="mono tabnum text-right text-white whitespace-nowrap">
                    {s.total_lots.toLocaleString()}
                  </td>
                  <td className="mono tabnum text-right whitespace-nowrap">
                    {s.closed_pct > 30 ? (
                      <span className="text-[var(--red)]">{s.closed_pct.toFixed(1)}%</span>
                    ) : (
                      <span className="text-zinc-400">{s.closed_pct.toFixed(1)}%</span>
                    )}
                  </td>
                  <td className="mono tabnum text-right whitespace-nowrap">
                    <span className={isHigh ? "text-[var(--red)] font-bold" : "text-zinc-300"}>
                      {s.high_risk_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="mono tabnum text-right whitespace-nowrap">
                    <span
                      style={{
                        color:
                          s.avg_risk_score >= 70
                            ? "var(--red)"
                            : s.avg_risk_score >= 40
                            ? "var(--amber)"
                            : "var(--emerald)",
                      }}
                    >
                      {s.avg_risk_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="mono tabnum text-right text-zinc-300 text-xs whitespace-nowrap">
                    {formatUZS(s.total_value_uzs)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-xs text-[var(--fg-dim)] mono">
        Manba: e-auksion.uz · Reyting har 24 soatda yangilanadi
      </p>
    </main>
  );
}
