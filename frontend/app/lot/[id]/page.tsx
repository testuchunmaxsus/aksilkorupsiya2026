import Link from "next/link";
import { notFound } from "next/navigation";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";
import { RiskBadge, RiskGauge } from "@/components/RiskBadge";
import { CategoryBars } from "@/components/CategoryBars";
import { PrintButton } from "@/components/PrintButton";
import { MLPanel } from "@/components/MLPanel";
import { VerdictHeader } from "@/components/Verdict";
import { ActionBox } from "@/components/ActionBox";

export const dynamic = "force-dynamic";

export default async function LotDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const lotId = parseInt(id, 10);
  if (isNaN(lotId)) notFound();

  const data = await api.lot(lotId).catch(() => null);
  if (!data) notFound();

  const { lot, related } = data;
  const flags = lot.flags || [];
  const discount =
    lot.start_price && lot.sold_price
      ? ((lot.start_price - lot.sold_price) / lot.start_price) * 100
      : null;

  const pepFlag = flags.find(
    (f) => f.type === "pep_seller" || f.type === "pep_family_match"
  ) as any;

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      {/* Breadcrumb + actions */}
      <div className="flex items-center justify-between no-print mb-6">
        <nav className="kicker flex items-center gap-2">
          <Link href="/" className="hover:text-[var(--primary)]">BOSH</Link>
          <span className="text-[var(--fg-dim)]">/</span>
          <Link href="/lots" className="hover:text-[var(--primary)]">LOTLAR</Link>
          <span className="text-[var(--fg-dim)]">/</span>
          <span className="text-[var(--fg)]">#{lot.id}</span>
        </nav>
        <PrintButton />
      </div>

      <div className="print-only mb-4">
        <div className="kicker">AUKSIONWATCH · TERGOV HISOBOTI</div>
        <div className="mono text-xs text-[var(--fg-dim)] mt-1">
          Hisobot sanasi: {new Date().toISOString().slice(0, 10)} · Lot #{lot.id}
        </div>
      </div>

      {/* TITLE — sodda, qisqa */}
      <header className="mb-4">
        <div className="kicker mb-2">
          LOT №{lot.id}
          {lot.region && (
            <>
              {" · "}
              {REGION_NAMES[lot.region] || lot.region}
            </>
          )}
          {lot.district ? ` · ${lot.district.toUpperCase()}` : ""}
        </div>
        <h1 className="headline text-2xl md:text-3xl text-[var(--fg)]">
          {lot.title || lot.lot_type || `Lot #${lot.id}`}
        </h1>
        {lot.address && (
          <p className="mt-2 text-[var(--fg-mute)] text-sm">📍 {lot.address}</p>
        )}
        <div className="mt-3 flex items-center gap-4 flex-wrap text-xs">
          <a
            href={lot.url}
            target="_blank"
            rel="noreferrer"
            className="link-u"
          >
            🔗 Manba: e-auksion.uz
          </a>
          {lot.scraped_at && (
            <span className="text-[var(--fg-dim)] mono">
              YIG&apos;ILGAN: {String(lot.scraped_at).slice(0, 10)}
            </span>
          )}
        </div>
      </header>

      {/* SODDA TIL VERDICT — eng tepada, har kim tushunadi */}
      <VerdictHeader lot={lot} />

      {/* AI XULOSA (agar mavjud bo'lsa) */}
      {lot.ai_summary && (
        <div className="mt-3 rounded-xl border border-[var(--line)] bg-[var(--bg-soft)] p-4 text-sm text-[var(--fg)]">
          <span className="kicker block mb-1">AI XULOSA</span>
          {lot.ai_summary}
        </div>
      )}

      {/* TEXNIK TAFSILOT — yashirin (collapsible). Default: yopiq. */}
      <details className="mt-4 group no-print">
        <summary className="cursor-pointer text-sm text-[var(--fg-mute)] hover:text-[var(--primary)] inline-flex items-center gap-2 list-none">
          <span className="inline-block w-4 transition-transform group-open:rotate-90">
            ▶
          </span>
          Texnik tafsilot ko&apos;rish (risk score, ML ensemble, kategoriyalar)
        </summary>
        <div className="card p-6 mt-3">
          <RiskGauge score={lot.risk_score} level={lot.risk_level} />
        </div>
      </details>

      {/* PEP MATCH BANNER */}
      {pepFlag?.pep && (
        <section className="mt-4 rounded-xl border border-purple-200 bg-purple-50 p-5">
          <div className="flex items-baseline gap-2 mb-2">
            <span className="pill" style={{ background: "#f3e8ff", color: "#7e22ce", borderColor: "transparent" }}>
              PEP MATCH
            </span>
            <span className="kicker text-purple-700">
              FATF R12 · EU 4-AML · UNCAC Art.8
            </span>
          </div>
          <h2 className="font-bold text-xl text-[var(--fg)]">
            {pepFlag.pep.pep_name}
          </h2>
          {pepFlag.pep.case_summary && (
            <p className="mt-2 text-sm text-[var(--fg-mute)] leading-relaxed">
              {pepFlag.pep.case_summary}
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-3 text-xs">
            <span className="mono text-purple-700">
              Mos kelish: {Math.round((pepFlag.pep.similarity || 0) * 100)}%
            </span>
            <span className="mono text-[var(--fg-mute)]">
              Tur: {pepFlag.pep.match_type}
            </span>
            {pepFlag.pep.case_url && (
              <a
                href={pepFlag.pep.case_url}
                target="_blank"
                rel="noreferrer"
                className="link-u text-purple-700"
              >
                Tashqi manba ↗
              </a>
            )}
          </div>
        </section>
      )}

      {/* PRICE STRIP */}
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <PriceCell label="Boshlang'ich" value={formatUZS(lot.start_price)} />
        <PriceCell
          label="Sotuv"
          value={formatUZS(lot.sold_price)}
          color={discount && discount > 30 ? "var(--red)" : undefined}
        />
        <PriceCell
          label="Diskont"
          value={discount != null ? `${discount.toFixed(1)}%` : "—"}
          color={discount && discount > 30 ? "var(--red)" : undefined}
        />
        <PriceCell
          label="Baholangan"
          value={formatUZS(lot.appraised_price)}
          color="var(--primary)"
        />
      </section>

      {/* MAIN GRID */}
      <div className="mt-6 grid lg:grid-cols-12 gap-6">
        {/* LEFT — facts */}
        <section className="lg:col-span-7 space-y-6">
          <div className="card overflow-hidden">
            <div className="border-b border-[var(--line)] px-5 py-3 bg-[var(--bg-soft)]">
              <div className="kicker">FAKTLAR · DALILLAR</div>
              <div className="font-bold text-[var(--fg)]">
                Lot ma&apos;lumotlari
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[var(--line-soft)]">
              <Facts
                rows={[
                  ["Lot turi", lot.lot_type_specific || lot.lot_type],
                  ["Auksion turi", lot.auction_type === "closed" ? "🔒 YOPIQ" : lot.auction_type === "open" ? "✓ Ochiq" : "⚪ Aniqlanmagan"],
                  ["Auksion uslubi", lot.auction_style],
                  ["Ishtirokchilar", lot.bidders_count ?? "—"],
                  ["Ko'rishlar", lot.views ?? "—"],
                  ["To'lov muddati", lot.installment_months ? `${lot.installment_months} oy` : "—"],
                ]}
              />
              <Facts
                rows={[
                  ["Sotuvchi", lot.seller_name || lot.seller_hint || "—"],
                  ["Boshlanish", lot.start_time],
                  ["Tugash", lot.end_time || lot.deadline],
                  ["Holat", lot.status],
                  ["Qadam bahosi", formatUZS(lot.step_price)],
                  ["Auksionga kelgan", lot.times_auctioned ? `${lot.times_auctioned} marta` : "—"],
                ]}
              />
            </div>
          </div>

          {related.length > 0 && (
            <div className="card overflow-hidden">
              <div className="border-b border-[var(--line)] px-5 py-3 bg-[var(--bg-soft)] flex items-end justify-between">
                <div>
                  <div className="kicker">SOTUVCHI TARIXI</div>
                  <div className="font-bold text-[var(--fg)]">
                    Boshqa lotlar
                  </div>
                </div>
                {lot.seller_id && (
                  <Link
                    href={`/seller/${lot.seller_id}`}
                    className="kicker hover:text-[var(--primary)]"
                  >
                    HAMMASI →
                  </Link>
                )}
              </div>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Lot</th>
                    <th>Boshlang&apos;ich</th>
                    <th>Auksion</th>
                    <th className="text-right">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {related.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <Link href={`/lot/${r.id}`} className="block">
                          <div className="mono text-xs text-[var(--fg-dim)]">#{r.id}</div>
                          <div className="text-[var(--fg)] hover:text-[var(--primary)] line-clamp-1 max-w-md">
                            {r.title || r.lot_type || "—"}
                          </div>
                        </Link>
                      </td>
                      <td className="mono tabnum text-[var(--fg-mute)]">
                        {formatUZS(r.start_price)}
                      </td>
                      <td>
                        {r.auction_type === "closed" ? (
                          <span className="pill red">YOPIQ</span>
                        ) : (
                          <span className="pill">Ochiq</span>
                        )}
                      </td>
                      <td className="text-right">
                        <RiskBadge score={r.risk_score} level={r.risk_level} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* RIGHT — flags + categories */}
        <aside className="lg:col-span-5 space-y-4">
          <MLPanel lot={lot} />
          <CategoryBars categories={lot.categories} total={lot.risk_score} />

          <div className="card overflow-hidden">
            <div className="border-b border-[var(--line)] px-5 py-3 bg-[var(--bg-soft)] flex items-center justify-between">
              <div>
                <div className="kicker">SHUBHALI BELGILAR</div>
                <div className="font-bold text-[var(--fg)]">
                  Aniqlangan {flags.length} signal
                </div>
              </div>
              <div
                className="text-3xl font-bold tabnum"
                style={{
                  color:
                    lot.risk_level === "high"
                      ? "var(--red)"
                      : lot.risk_level === "medium"
                      ? "var(--amber)"
                      : "var(--emerald)",
                }}
              >
                {Math.round(lot.risk_score)}
              </div>
            </div>
            {flags.length === 0 ? (
              <div className="px-5 py-10 text-center">
                <div className="text-emerald-500 text-3xl">✓</div>
                <p className="mt-2 text-[var(--fg-mute)] text-sm">
                  Bu lotda shubhali belgi topilmadi.
                </p>
              </div>
            ) : (
              <ul className="divide-y divide-[var(--line-soft)]">
                {flags.map((f, i) => (
                  <li key={f.type + i} className="px-5 py-4">
                    <div className="flex items-start gap-3">
                      <span className="mono text-xs text-[var(--fg-dim)] tabnum mt-0.5 w-5">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-baseline gap-2 flex-wrap">
                            {f.category && (
                              <span
                                className="pill"
                                style={{
                                  background:
                                    f.category === "A" ? "#fff7ed"
                                    : f.category === "B" ? "#faf5ff"
                                    : f.category === "C" ? "#fef2f2"
                                    : f.category === "D" ? "#fefce8"
                                    : "#ecfeff",
                                  color:
                                    f.category === "A" ? "#c2410c"
                                    : f.category === "B" ? "#7e22ce"
                                    : f.category === "C" ? "#b91c1c"
                                    : f.category === "D" ? "#a16207"
                                    : "#0e7490",
                                  borderColor: "transparent",
                                }}
                              >
                                {f.category}
                              </span>
                            )}
                            <span className="font-semibold text-[var(--fg)] text-sm">
                              {f.title}
                            </span>
                          </div>
                          <div className="text-right whitespace-nowrap">
                            <div className="mono text-xs text-[var(--red)] font-bold">
                              +{f.score}
                              {f.weight !== undefined && f.weight !== 1 && (
                                <span className="text-[var(--fg-dim)] font-normal"> × {f.weight}</span>
                              )}
                            </div>
                            {f.weighted_score !== undefined && f.weighted_score !== f.score && (
                              <div className="mono text-[10px] text-[var(--fg-dim)]">
                                = {f.weighted_score}
                              </div>
                            )}
                          </div>
                        </div>
                        <p className="mt-1 text-xs text-[var(--fg-mute)] leading-relaxed">
                          {f.desc}
                        </p>
                        {(f.formula || f.ref) && (
                          <div className="mt-2 grid grid-cols-1 gap-1 text-[10px] mono leading-relaxed">
                            {f.formula && (
                              <div>
                                <span className="text-[var(--fg-dim)]">FORMULA</span>
                                <span className="ml-2 text-[var(--fg)] bg-[var(--bg-soft)] px-1.5 py-0.5 rounded">
                                  {f.formula}
                                </span>
                              </div>
                            )}
                            {f.fields && f.fields.length > 0 && (
                              <div>
                                <span className="text-[var(--fg-dim)]">FIELDS</span>
                                <span className="ml-2 text-[var(--fg-mute)]">
                                  {f.fields.join(", ")}
                                </span>
                              </div>
                            )}
                            {f.ref && (
                              <div>
                                <span className="text-[var(--fg-dim)]">MANBA</span>
                                {f.ref_url ? (
                                  <a
                                    href={f.ref_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="ml-2 link-u"
                                  >
                                    {f.ref} ↗
                                  </a>
                                ) : (
                                  <span className="ml-2 text-[var(--fg-mute)]">{f.ref}</span>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

        </aside>
      </div>

      {/* HARAKAT QILIM TUGMALARI — eng pastda, foydalanuvchi nima qilishni biladi */}
      <div className="mt-8">
        <ActionBox lot={lot} />
      </div>
    </main>
  );
}

function PriceCell({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="card p-4">
      <div className="kicker">{label}</div>
      <div
        className="mt-2 text-xl md:text-2xl font-bold tabnum"
        style={{ color: color || "var(--fg)" }}
      >
        {value}
      </div>
    </div>
  );
}

function Facts({ rows }: { rows: [string, any][] }) {
  return (
    <dl className="divide-y divide-[var(--line-soft)]">
      {rows.map(([k, v]) => (
        <div key={k} className="grid grid-cols-5 gap-3 px-5 py-2.5">
          <dt className="col-span-2 kicker">{k}</dt>
          <dd className="col-span-3 text-sm text-[var(--fg)] mono tabnum truncate">
            {v ?? "—"}
          </dd>
        </div>
      ))}
    </dl>
  );
}
