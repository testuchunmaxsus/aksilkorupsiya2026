// Sotuvchilar reytingi — egalik turi bo'yicha tab/filter bilan.
// Sud ijrochilari ofislari texnik jihatdan eng ko'p lot sotadi —
// ularni "davlat sotuvchi" deb ko'rsatish judge'ni chalg'itadi.
// Shu uchun: Davlat (Davaktiv) / Musodara (sud) / Yuridik shaxs alohida.
import Link from "next/link";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";
import { OwnershipBadge } from "@/components/OwnershipBadge";
import { maskSellerName } from "@/lib/pii";

export const dynamic = "force-dynamic";

const TABS = [
  { key: "state", label: "🏛 Davlat (Davaktiv)", desc: "Asosiy monitoring obyekti" },
  { key: "confiscated", label: "⚖ Musodara (sud/MIB)", desc: "Sud orqali olingan shaxsiy mol-mulk" },
  { key: "private", label: "🏢 Yuridik shaxs", desc: "Bankrot biznes / banklar" },
  { key: "all", label: "Hammasi", desc: "Barcha sotuvchilar" },
] as const;

export default async function SellersPage({
  searchParams,
}: {
  searchParams: Promise<{ ownership?: string }>;
}) {
  const sp = await searchParams;
  const activeTab = sp.ownership || "state"; // default — davlat
  const ownershipParam = activeTab === "all" ? undefined : activeTab;
  const data = await api.sellers(50, ownershipParam).catch(() => ({ items: [] }));
  const items = data.items;

  const totalLots = items.reduce((s, x) => s + x.total_lots, 0);
  const top3 = items.slice(0, 3).reduce((s, x) => s + x.total_lots, 0);
  const top3pct = totalLots > 0 ? (top3 / totalLots) * 100 : 0;

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker">REYTING · LEADERBOARD</div>
        <h1 className="headline mt-2 text-4xl text-[var(--fg)]">
          Sotuvchilar reytingi
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-[var(--fg-mute)]">
          Lotlar soni bo&apos;yicha eng yirik sotuvchilar ro&apos;yxati. Egalik turi
          bo&apos;yicha alohida tab&apos;lar — chunki sud ijrochilari va Davaktiv
          turli mexanizmlar bilan ishlaydi va ularni bir xil reytingda
          ko&apos;rsatish chalkash bo&apos;ladi.
        </p>

        {/* Ownership tab'lar */}
        <nav className="mt-5 flex flex-wrap gap-2 border-b border-[var(--line)] pb-1 -mb-px">
          {TABS.map((t) => {
            const isActive = activeTab === t.key;
            return (
              <Link
                key={t.key}
                href={`/sellers?ownership=${t.key}`}
                className={
                  "px-4 py-2 text-sm font-medium border-b-2 transition-colors " +
                  (isActive
                    ? "border-[var(--primary)] text-[var(--primary)]"
                    : "border-transparent text-[var(--fg-mute)] hover:text-[var(--primary)]")
                }
                title={t.desc}
              >
                {t.label}
              </Link>
            );
          })}
        </nav>

        {top3pct > 50 && activeTab === "state" && (
          <div className="mt-4 inline-flex items-center gap-2 rounded border border-[var(--red)]/40 bg-[var(--red)]/5 px-3 py-1.5 mono text-xs">
            <span className="text-[var(--red)]">●</span>
            <span className="text-[var(--fg-mute)]">
              TOP 3 davlat sotuvchi {top3.toLocaleString()} ta lot ({top3pct.toFixed(1)}%) ni
              nazorat qiladi — <strong className="text-[var(--red)]">state capture</strong> belgisi
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
              <th>Egalik</th>
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
                    <Link href={`/seller/${s.seller_id}`} className="block group">
                      <div className="text-[var(--fg)] link-u line-clamp-1 max-w-md">
                        {s.seller_name
                          ? maskSellerName(s.seller_name, s.seller_hint)
                          : `Sotuvchi #${s.seller_id}`}
                      </div>
                      <div className="mono text-[10px] text-[var(--fg-dim)]">
                        ID: {s.seller_id}
                      </div>
                    </Link>
                  </td>
                  <td>
                    <OwnershipBadge seller_hint={s.seller_hint} size="sm" />
                  </td>
                  <td className="text-[var(--fg-mute)] text-sm whitespace-nowrap">
                    {s.region ? REGION_NAMES[s.region] || s.region : "—"}
                  </td>
                  <td className="mono tabnum text-right text-[var(--fg)] whitespace-nowrap">
                    {s.total_lots.toLocaleString()}
                  </td>
                  <td className="mono tabnum text-right whitespace-nowrap">
                    {s.closed_pct > 30 ? (
                      <span className="text-[var(--red)]">{s.closed_pct.toFixed(1)}%</span>
                    ) : (
                      <span className="text-[var(--fg-mute)]">{s.closed_pct.toFixed(1)}%</span>
                    )}
                  </td>
                  <td className="mono tabnum text-right whitespace-nowrap">
                    <span className={isHigh ? "text-[var(--red)] font-bold" : "text-[var(--fg-mute)]"}>
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
                  <td className="mono tabnum text-right text-[var(--fg-mute)] text-xs whitespace-nowrap">
                    {formatUZS(s.total_value_uzs)}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && (
              <tr>
                <td colSpan={9} className="text-center text-[var(--fg-dim)] py-12">
                  Bu egalik turi bo&apos;yicha sotuvchi topilmadi.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-xs text-[var(--fg-dim)] mono">
        Manba: e-auksion.uz · Reyting har 24 soatda yangilanadi · Egalik turi
        seller_hint maydonidan aniqlanadi
      </p>
    </main>
  );
}
