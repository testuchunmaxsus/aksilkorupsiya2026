import Link from "next/link";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

export const dynamic = "force-dynamic";

export default async function PEPPage() {
  const data = await api
    .lots({ limit: 200 })
    .catch(() => ({ count: 0, items: [] }));

  // Filter lots with PEP signals
  const pepLots = data.items.filter((lot) =>
    (lot.flags || []).some(
      (f) => f.type === "pep_seller" || f.type === "pep_family_match"
    )
  );

  // Group by PEP
  const byPep: Record<
    string,
    {
      id: string;
      name: string;
      lots: typeof pepLots;
      case_url?: string;
      case_summary?: string;
      category?: string;
    }
  > = {};
  for (const lot of pepLots) {
    const f = (lot.flags || []).find((x: any) => x.pep) as any;
    if (!f?.pep) continue;
    const id = f.pep.pep_id;
    if (!byPep[id]) {
      byPep[id] = {
        id,
        name: f.pep.pep_name,
        lots: [],
        case_url: f.pep.case_url,
        case_summary: f.pep.case_summary,
        category: f.pep.category,
      };
    }
    byPep[id].lots.push(lot);
  }

  const sortedPeps = Object.values(byPep).sort(
    (a, b) => b.lots.length - a.lots.length
  );

  const CATEGORY_LABEL: Record<string, string> = {
    executive: "Ijroiya hokimiyat",
    "buyer-of-interest": "Yirik buyurtmachi",
    legislative: "Qonun chiqaruvchi",
    judicial: "Sud hokimiyati",
  };

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker text-purple-700">
          POLITICALLY EXPOSED PERSONS · FATF R12
        </div>
        <h1 className="headline mt-2 text-4xl text-[var(--fg)]">
          Mansabdor / PEP signal&apos;lari
        </h1>
        <p className="mt-3 max-w-3xl text-[var(--fg-mute)]">
          AuksionWatch FATF Recommendation 12 va EU 4-AML Directive bo&apos;yicha
          siyosatchilar va mansabdorlar (PEP) ishtirokini aniqlaydi. Bu —
          Akmalxon Ortiqov keysidagi haqiqiy korrupsiya manbai. Sotuvchi nomi
          watchlist&apos;dagi shaxs bilan to&apos;liq, qisman yoki familiya bilan mos
          kelsa flag chaqiriladi.
        </p>
      </header>

      <div className="mt-8 space-y-6">
        {sortedPeps.length === 0 ? (
          <div className="card p-10 text-center text-[var(--fg-mute)]">
            Hozircha PEP-bog&apos;liq lot topilmadi.
          </div>
        ) : (
          sortedPeps.map((p) => (
            <div key={p.id} className="card overflow-hidden">
              <div
                className="border-b border-[var(--line)] px-6 py-5 flex items-start justify-between gap-4"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(168,85,247,0.06), rgba(168,85,247,0.02))",
                }}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className="pill"
                      style={{
                        background: "#f3e8ff",
                        color: "#7e22ce",
                        borderColor: "transparent",
                      }}
                    >
                      PEP
                    </span>
                    {p.category && (
                      <span className="kicker text-purple-700">
                        {CATEGORY_LABEL[p.category] || p.category}
                      </span>
                    )}
                  </div>
                  <h2 className="headline mt-2 text-2xl text-[var(--fg)]">
                    {p.name}
                  </h2>
                  {p.case_summary && (
                    <p className="mt-2 text-sm text-[var(--fg-mute)] max-w-2xl">
                      {p.case_summary}
                    </p>
                  )}
                  {p.case_url && (
                    <a
                      href={p.case_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block link-u text-xs"
                    >
                      Tashqi manba ↗
                    </a>
                  )}
                </div>
                <div className="text-right">
                  <div className="kicker">FLAGGED</div>
                  <div
                    className="text-3xl font-bold tabnum"
                    style={{ color: "#7e22ce" }}
                  >
                    {p.lots.length}
                  </div>
                  <div className="kicker text-[var(--fg-dim)]">xavfli lot</div>
                </div>
              </div>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Lot</th>
                    <th>Hudud</th>
                    <th className="text-right">Boshlang&apos;ich</th>
                    <th className="text-right">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {p.lots.slice(0, 10).map((lot) => (
                    <tr key={lot.id}>
                      <td>
                        <Link href={`/lot/${lot.id}`} className="block">
                          <div className="mono text-xs text-[var(--fg-dim)]">
                            #{lot.id}
                          </div>
                          <div className="text-[var(--fg)] hover:text-[var(--primary)] line-clamp-1 max-w-md">
                            {lot.title || lot.lot_type || "—"}
                          </div>
                        </Link>
                      </td>
                      <td className="text-[var(--fg-mute)] whitespace-nowrap text-sm">
                        {lot.region ? REGION_NAMES[lot.region] || lot.region : "—"}
                      </td>
                      <td className="mono tabnum text-right text-[var(--fg-mute)] whitespace-nowrap">
                        {formatUZS(lot.start_price)}
                      </td>
                      <td className="text-right whitespace-nowrap">
                        <RiskBadge score={lot.risk_score} level={lot.risk_level} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {p.lots.length > 10 && (
                <div className="border-t border-[var(--line)] px-5 py-2.5 text-center kicker bg-[var(--bg-soft)]">
                  +{p.lots.length - 10} ta yana
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <section
        className="mt-10 rounded-xl border p-5 text-sm text-[var(--fg-mute)]"
        style={{
          borderColor: "rgba(168,85,247,0.25)",
          background: "rgba(168,85,247,0.05)",
        }}
      >
        <div className="kicker text-purple-700 mb-2">DISCLAIMER · METODOLOGIYA</div>
        <p>
          PEP watchlist hozirgi MVP&apos;da qo&apos;lda yuborilgan demo dataset.
          Production versiyada{" "}
          <a
            href="https://www.opensanctions.org/"
            target="_blank"
            rel="noreferrer"
            className="link-u"
          >
            OpenSanctions API
          </a>
          {" "}+{" "}
          <a
            href="https://anticorruption.uz/"
            target="_blank"
            rel="noreferrer"
            className="link-u"
          >
            anticorruption.uz mansabdor deklaratsiyalari
          </a>
          {" "}bilan integratsiya qilinadi. Aniqlangan mos kelish — qonuniy
          ayb degani emas, faqat tekshirish uchun ko&apos;rsatma. FATF
          Recommendation 12 va EU 4-AML Directive standartlariga muvofiq.
        </p>
      </section>
    </main>
  );
}
