import Link from "next/link";
import { api, formatUZS, REGION_NAMES } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { RiskBadge } from "@/components/RiskBadge";
import { RegionBars } from "@/components/RegionBars";
import { TrendChart } from "@/components/TrendChart";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [stats, redToday, timeline] = await Promise.all([
    api.stats().catch(() => null),
    api.redFlagsToday(8).catch(() => ({ items: [] })),
    api.timeline().catch(() => ({ series: [] })),
  ]);

  return (
    <main>
      {/* HERO — gov-portal style */}
      <section className="hero-gradient border-b border-[var(--line)]">
        <div className="mx-auto max-w-7xl px-6 py-14 md:py-20 grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7">
            <span className="pill red mb-5">
              <span className="inline-block h-2 w-2 rounded-full bg-[var(--red)] live-dot" />
              Real-vaqt monitoring · 11,224 lot tahlilda
            </span>
            <h1 className="headline mt-2 text-4xl md:text-6xl text-[var(--fg)] leading-[1.05]">
              Har bir auksion <br />
              <span className="text-[var(--primary)]">ochiq nazoratda</span>
              <span className="text-[var(--red)]">.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base md:text-lg text-[var(--fg-mute)] leading-relaxed">
              Davlat mol-mulki auksionlaridagi shubhali sxemalarni xalqaro
              standartlar (OECD, UNCAC, OCDS, FATF) asosida AI yordamida
              aniqlovchi mustaqil monitoring tizimi.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/map" className="btn btn-primary">
                Xaritani ochish
              </Link>
              <Link href="/lots?risk_level=high" className="btn btn-outline">
                Qizil bayroqlar →
              </Link>
              <Link href="/methodology" className="btn btn-outline">
                Metodologiya
              </Link>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="card p-6 bg-white">
              <div className="flex items-center justify-between mb-4">
                <div className="kicker text-[var(--primary)]">ORTIQOV-2026 KEYS</div>
                <span className="pill red">130 mlrd zarar</span>
              </div>
              <h3 className="font-bold text-[var(--fg)] text-lg mb-2">
                Yopiq auksionda yer 250 → 120 mlrd
              </h3>
              <p className="text-sm text-[var(--fg-mute)] leading-relaxed">
                2026-yanvar: Davlat aktivlarini boshqarish agentligi
                rahbari hibsga olindi. Bunday sxemalarni biz <strong>avval</strong> ushlay olamiz.
              </p>
              <div className="mt-4 grid grid-cols-3 gap-2 pt-4 border-t border-[var(--line)]">
                <div>
                  <div className="text-2xl font-bold text-[var(--red)] tabnum">5/5</div>
                  <div className="text-[10px] text-[var(--fg-dim)] uppercase tracking-wide mt-0.5">Toifada signal</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--primary)] tabnum">100</div>
                  <div className="text-[10px] text-[var(--fg-dim)] uppercase tracking-wide mt-0.5">Risk score</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--fg)] tabnum">45+</div>
                  <div className="text-[10px] text-[var(--fg-dim)] uppercase tracking-wide mt-0.5">Indikator</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* STATS BAND */}
      {stats && (
        <section className="mx-auto max-w-7xl px-6 -mt-8 relative z-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="JAMI LOTLAR"
              value={stats.total.toLocaleString()}
              hint={`${stats.by_region.length} ta hudud`}
              icon="📊"
            />
            <StatCard
              label="QIZIL BAYROQLAR"
              value={stats.high_risk.toLocaleString()}
              hint={`+${stats.medium_risk} ta o'rta xavf`}
              accent="danger"
              icon="🚩"
            />
            <StatCard
              label="YOPIQ AUKSIONLAR"
              value={stats.closed_auctions.toLocaleString()}
              hint={`${((stats.closed_auctions / Math.max(1, stats.total)) * 100).toFixed(1)}% jami`}
              accent="warn"
              icon="🔒"
            />
            <StatCard
              label="XAVFLI QIYMAT"
              value={formatUZS(stats.high_risk_value_uzs).replace(" so'm", "")}
              hint={`Jami: ${formatUZS(stats.total_value_uzs)}`}
              accent="danger"
              icon="💰"
            />
          </div>
        </section>
      )}

      {/* SERVICE TILES — my.gov.uz style */}
      <section className="mx-auto max-w-7xl px-6 mt-16">
        <div className="flex items-end justify-between mb-6">
          <div>
            <div className="kicker">XIZMATLAR</div>
            <h2 className="headline text-2xl md:text-3xl text-[var(--fg)] mt-1">
              Asosiy bo&apos;limlar
            </h2>
          </div>
          <Link href="/methodology" className="btn btn-outline hidden md:inline-flex">
            Hammasi haqida →
          </Link>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <Link href="/lots" className="service-tile">
            <span className="icon">📋</span>
            <div>
              <div className="font-semibold text-[var(--fg)]">Lotlar reestri</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1 leading-relaxed">
                Filtr + qidiruv + risk
              </div>
            </div>
          </Link>
          <Link href="/map" className="service-tile">
            <span className="icon">🗺️</span>
            <div>
              <div className="font-semibold text-[var(--fg)]">Xarita</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1 leading-relaxed">
                Geografik taqsimot
              </div>
            </div>
          </Link>
          <Link href="/sellers" className="service-tile">
            <span className="icon">🏛️</span>
            <div>
              <div className="font-semibold text-[var(--fg)]">Sotuvchilar</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1 leading-relaxed">
                TOP reyting + tarix
              </div>
            </div>
          </Link>
          <Link href="/network" className="service-tile">
            <span className="icon">🕸️</span>
            <div>
              <div className="font-semibold text-[var(--fg)]">Tarmoq grafi</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1 leading-relaxed">
                Sotuvchi-hudud aloqalar
              </div>
            </div>
          </Link>
          <Link href="/pep" className="service-tile danger">
            <span className="icon">⚠️</span>
            <div>
              <div className="font-semibold text-[var(--fg)]">PEP signal&apos;lari</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1 leading-relaxed">
                Mansabdor ishtiroki
              </div>
            </div>
          </Link>
          <Link href="/methodology" className="service-tile success">
            <span className="icon">📚</span>
            <div>
              <div className="font-semibold text-[var(--fg)]">Metodologiya</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1 leading-relaxed">
                5 toifa, 18+ rule
              </div>
            </div>
          </Link>
        </div>
      </section>

      {/* TIMELINE + RED FLAGS */}
      <section className="mx-auto max-w-7xl px-6 mt-12 grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card overflow-hidden">
          <div className="border-b border-[var(--line)] px-5 py-4 bg-[var(--bg-soft)] flex items-end justify-between">
            <div>
              <div className="kicker">VAQT TRENDI</div>
              <div className="font-bold text-lg text-[var(--fg)]">
                Auksion dinamikasi
              </div>
            </div>
            <div className="text-right text-xs mono text-[var(--fg-dim)]">
              {timeline.series.length} oy
            </div>
          </div>
          <div className="px-2 py-4">
            <TrendChart data={timeline.series} />
          </div>
        </div>

        <div className="card overflow-hidden">
          <div className="border-b border-[var(--line)] px-5 py-4 bg-[var(--bg-soft)] flex items-end justify-between">
            <div>
              <div className="kicker">BUGUNGI</div>
              <div className="font-bold text-lg text-[var(--fg)]">
                Qizil bayroqlar
              </div>
            </div>
            <Link href="/lots?risk_level=high" className="kicker hover:text-[var(--primary)]">
              →
            </Link>
          </div>
          <ul className="divide-y divide-[var(--line-soft)] max-h-[330px] overflow-auto">
            {redToday.items.map((lot) => (
              <li key={lot.id}>
                <Link
                  href={`/lot/${lot.id}`}
                  className="block px-5 py-3 hover:bg-[var(--primary-soft)] transition-colors"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="mono text-[10px] text-[var(--fg-dim)]">
                        #{lot.id}
                      </div>
                      <div className="text-sm font-medium text-[var(--fg)] truncate">
                        {lot.title || lot.lot_type || "Nomsiz lot"}
                      </div>
                      <div className="mono text-xs text-[var(--fg-mute)] mt-0.5">
                        {lot.region ? REGION_NAMES[lot.region] || lot.region : "—"}
                        {" · "}
                        {formatUZS(lot.start_price)}
                      </div>
                    </div>
                    <RiskBadge score={lot.risk_score} level={lot.risk_level} />
                  </div>
                </Link>
              </li>
            ))}
            {redToday.items.length === 0 && (
              <li className="px-5 py-10 text-center text-[var(--fg-dim)]">
                Backend ulanmagan
              </li>
            )}
          </ul>
        </div>
      </section>

      {/* REGION BARS */}
      {stats && (
        <section className="mx-auto max-w-7xl px-6 mt-12">
          <RegionBars
            rows={stats.by_region}
            highRows={stats.high_risk_by_region}
          />
        </section>
      )}

      {/* METHODOLOGY 6 SIGNAL */}
      <section className="mx-auto max-w-7xl px-6 mt-16 mb-10">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <div className="kicker">METODOLOGIYA</div>
          <h2 className="headline text-3xl text-[var(--fg)] mt-2">
            AI 18+ ta avtomatik signal asosida
            <span className="text-[var(--primary)]"> xulosa chiqaradi</span>
          </h2>
          <p className="mt-3 text-[var(--fg-mute)]">
            Har signal — xalqaro standartga (OECD, World Bank, Fazekas CRI, FATF) asoslangan.
            Hech bir signal &quot;qora quti&quot; emas: formula, fields, manba — ochiq.
          </p>
        </div>
        <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { c: "A", title: "Yopiq auksion", w: 30, s: "Past shaffoflik" },
            { c: "B", title: "Monopol sotuvchi", w: 30, s: "Kelishuv" },
            { c: "C", title: "1 ishtirokchi", w: 25, s: "Bid-rigging" },
            { c: "C", title: "Combo CRI", w: 20, s: "Bid-rigging (bonus)" },
            { c: "D", title: "Past baho", w: 35, s: "Firibgarlik" },
            { c: "B", title: "PEP match", w: 35, s: "Insider" },
          ].map((s, i) => (
            <div key={i} className="card p-4 card-hover">
              <div className="flex items-center justify-between mb-2">
                <span className="pill primary">{s.c}</span>
                <span className="mono text-xs text-[var(--red)] font-bold">+{s.w}</span>
              </div>
              <div className="font-semibold text-[var(--fg)] text-sm">{s.title}</div>
              <div className="text-xs text-[var(--fg-mute)] mt-1">{s.s}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
