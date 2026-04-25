import Link from "next/link";
import { notFound } from "next/navigation";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

export const dynamic = "force-dynamic";

export default async function SellerDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const sellerId = parseInt(id, 10);
  if (isNaN(sellerId)) notFound();

  const data = await api.seller(sellerId).catch(() => null);
  if (!data) notFound();

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <div className="kicker">
        <Link href="/" className="hover:text-white">BOSH</Link>
        <span className="mx-2 text-[var(--fg-dim)]">/</span>
        <Link href="/sellers" className="hover:text-white">SOTUVCHILAR</Link>
        <span className="mx-2 text-[var(--fg-dim)]">/</span>
        <span className="text-white">#{sellerId}</span>
      </div>

      <header className="mt-6 border-b border-[var(--line)] pb-8">
        <div className="kicker">SOTUVCHI · ID {sellerId}</div>
        <h1 className="headline mt-2 text-4xl md:text-5xl text-white">
          {data.seller_name || `Sotuvchi #${sellerId}`}
        </h1>
        {data.region && (
          <p className="mt-2 byline text-[var(--fg-mute)]">
            {REGION_NAMES[data.region] || data.region}
          </p>
        )}
      </header>

      <section className="mt-8 grid grid-cols-2 md:grid-cols-4 border border-[var(--line)] divide-x divide-[var(--line)] bg-[var(--bg-elev)]">
        <Cell label="JAMI LOTLAR" value={data.total_lots.toLocaleString()} />
        <Cell
          label="YUQORI XAVF"
          value={`${data.high_risk_count.toLocaleString()} (${data.high_risk_pct}%)`}
          color={data.high_risk_pct >= 50 ? "var(--red)" : undefined}
        />
        <Cell
          label="YOPIQ AUKSION"
          value={`${data.closed_count.toLocaleString()} (${data.closed_pct}%)`}
          color={data.closed_pct >= 30 ? "var(--amber)" : undefined}
        />
        <Cell
          label="JAMI QIYMAT"
          value={formatUZS(data.total_value_uzs)}
        />
      </section>

      <section className="mt-10">
        <div className="flex items-end justify-between mb-4">
          <h2 className="headline text-2xl text-white">
            Eng xavfli lotlar
          </h2>
          <span className="kicker">TOP 50</span>
        </div>
        <div className="card overflow-hidden">
          <table className="tbl">
            <thead>
              <tr>
                <th>Lot</th>
                <th>Hudud</th>
                <th className="text-right">Boshlang&apos;ich</th>
                <th>Auksion</th>
                <th className="text-right">Risk</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((lot) => (
                <tr key={lot.id}>
                  <td>
                    <Link href={`/lot/${lot.id}`} className="block">
                      <div className="mono text-xs text-[var(--fg-dim)]">
                        #{lot.id}
                      </div>
                      <div className="text-zinc-100 link-u line-clamp-1 max-w-md">
                        {lot.title || lot.lot_type || "—"}
                      </div>
                    </Link>
                  </td>
                  <td className="text-zinc-300 whitespace-nowrap text-sm">
                    {lot.region ? REGION_NAMES[lot.region] || lot.region : "—"}
                  </td>
                  <td className="mono tabnum text-right text-zinc-200 whitespace-nowrap">
                    {formatUZS(lot.start_price)}
                  </td>
                  <td>
                    {lot.auction_type === "closed" ? (
                      <span className="mono text-[10px] tracking-widest text-[var(--red)] border border-[var(--red)]/40 px-1.5 py-0.5">
                        YOPIQ
                      </span>
                    ) : (
                      <span className="mono text-[10px] tracking-widest text-[var(--fg-dim)]">
                        OCHIQ
                      </span>
                    )}
                  </td>
                  <td className="text-right">
                    <RiskBadge score={lot.risk_score} level={lot.risk_level} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function Cell({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="px-5 py-5">
      <div className="kicker">{label}</div>
      <div
        className="headline mt-2 text-2xl md:text-3xl tabnum"
        style={{ color: color || "white" }}
      >
        {value}
      </div>
    </div>
  );
}
