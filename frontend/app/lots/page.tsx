import Link from "next/link";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";
import { OwnershipBadge } from "@/components/OwnershipBadge";
import { Pagination } from "@/components/Pagination";

export const dynamic = "force-dynamic";

const PER_PAGE = 50;

export default async function LotsPage({
  searchParams,
}: {
  searchParams: Promise<{
    risk_level?: string;
    auction_type?: string;
    region?: string;
    q?: string;
    page?: string;
    ownership?: string;
  }>;
}) {
  const sp = await searchParams;
  const page = Math.max(1, parseInt(sp.page || "1", 10) || 1);
  const offset = (page - 1) * PER_PAGE;

  const params: Record<string, string | number> = {
    limit: PER_PAGE,
    offset,
  };
  if (sp.risk_level) params.risk_level = sp.risk_level;
  if (sp.auction_type) params.auction_type = sp.auction_type;
  if (sp.region) params.region = sp.region;
  if (sp.q) params.q = sp.q;
  if (sp.ownership) params.ownership = sp.ownership;

  const data = await api.lots(params).catch(() => ({ count: 0, items: [] }));
  const activeFilter = sp.risk_level === "high";

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker">REESTR · DATABASE</div>
        <h1 className="headline mt-2 text-4xl text-white">
          {activeFilter ? "Qizil bayroqlar" : "Hamma lotlar"}
        </h1>
        <p className="mt-2 mono text-sm text-[var(--fg-mute)]">
          {data.count.toLocaleString()} ta natija topildi
          {data.count > PER_PAGE && (
            <> · sahifa <strong className="text-[var(--fg)]">{page}</strong> / {Math.ceil(data.count / PER_PAGE)}</>
          )}
        </p>
      </header>

      <form className="mt-6 flex flex-wrap items-center gap-2 border border-[var(--line)] bg-[var(--bg-elev)] p-3">
        <input
          name="q"
          defaultValue={sp.q || ""}
          placeholder="🔍  Sarlavha, manzil, lot raqami..."
          className="flex-1 min-w-[240px] bg-transparent border-0 outline-none px-3 py-2 text-sm text-zinc-100 placeholder:text-[var(--fg-dim)]"
        />
        <select
          name="risk_level"
          defaultValue={sp.risk_level || ""}
          className="bg-[var(--bg)] border border-[var(--line)] px-3 py-2 text-sm mono text-zinc-200"
        >
          <option value="">XAVF: HAMMASI</option>
          <option value="high">XAVF: YUQORI</option>
          <option value="medium">XAVF: O&apos;RTA</option>
          <option value="low">XAVF: OZ</option>
        </select>
        <select
          name="auction_type"
          defaultValue={sp.auction_type || ""}
          className="bg-[var(--bg)] border border-[var(--line)] px-3 py-2 text-sm mono text-zinc-200"
        >
          <option value="">AUKSION: HAMMASI</option>
          <option value="closed">AUKSION: YOPIQ</option>
          <option value="open">AUKSION: OCHIQ</option>
        </select>
        <select
          name="ownership"
          defaultValue={sp.ownership || ""}
          className="bg-[var(--bg)] border border-[var(--line)] px-3 py-2 text-sm mono text-zinc-200"
          title="Egalik turi: Davlat (Davaktiv) / Musodara (sud) / Yuridik shaxs"
        >
          <option value="">EGALIK: HAMMASI</option>
          <option value="state">🏛 DAVLAT MOL-MULKI</option>
          <option value="confiscated">⚖ MUSODARA (SUD/MIB)</option>
          <option value="private">🏢 YURIDIK SHAXS</option>
        </select>
        <button className="bg-[var(--red)] px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 mono tracking-wider">
          FILTR
        </button>
      </form>

      <div className="mt-6 card overflow-hidden">
        <table className="tbl">
          <thead>
            <tr>
              <th>Lot</th>
              <th>Hudud</th>
              <th className="text-right">Boshlang&apos;ich</th>
              <th className="text-right">Sotuv</th>
              <th>Auksion</th>
              <th className="text-right">Risk</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((lot) => (
              <tr key={lot.id}>
                <td>
                  <Link href={`/lot/${lot.id}`} className="block group">
                    <div className="mono text-xs text-[var(--fg-dim)] flex items-center gap-2">
                      <span>#{lot.id}</span>
                      <OwnershipBadge seller_hint={lot.seller_hint} size="sm" />
                    </div>
                    <div className="text-zinc-100 link-u line-clamp-1 max-w-md mt-1">
                      {lot.title || lot.lot_type}
                    </div>
                  </Link>
                </td>
                <td className="text-zinc-300 whitespace-nowrap text-sm">
                  {lot.region ? REGION_NAMES[lot.region] || lot.region : "—"}
                </td>
                <td className="mono tabnum text-zinc-200 text-right whitespace-nowrap">
                  {formatUZS(lot.start_price)}
                </td>
                <td className="mono tabnum text-zinc-200 text-right whitespace-nowrap">
                  {formatUZS(lot.sold_price)}
                </td>
                <td className="whitespace-nowrap">
                  {lot.auction_type === "closed" ? (
                    <span className="mono text-[10px] tracking-widest text-[var(--red)] border border-[var(--red)]/40 px-1.5 py-0.5">
                      YOPIQ
                    </span>
                  ) : lot.auction_type === "open" ? (
                    <span className="mono text-[10px] tracking-widest text-[var(--emerald)]">
                      OCHIQ
                    </span>
                  ) : (
                    <span
                      className="mono text-[10px] tracking-widest text-[var(--fg-dim)] border border-dashed border-[var(--line)] px-1.5 py-0.5 cursor-help"
                      title="Davaktiv Excel hisobotida 'auksion turi' maydoni yo'q. Aniqlash uchun e-auksion API'dan qo'shimcha ma'lumot kerak."
                    >
                      AKT NO&apos;MA&apos;LUM
                    </span>
                  )}
                </td>
                <td className="text-right whitespace-nowrap">
                  <RiskBadge score={lot.risk_score} level={lot.risk_level} />
                </td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-zinc-500 py-12">
                  Topilmadi.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Sahifalar boshqaruvi — filtrlar saqlanadi */}
      <Pagination
        total={data.count}
        page={page}
        perPage={PER_PAGE}
        basePath="/lots"
        searchParams={sp}
      />
    </main>
  );
}
