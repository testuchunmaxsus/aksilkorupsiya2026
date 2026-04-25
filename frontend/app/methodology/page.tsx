import Link from "next/link";

export const metadata = {
  title: "Metodologiya — AuksionWatch",
};

const CATEGORIES = [
  {
    code: "A",
    name: "Past shaffoflik",
    full: "Low Transparency",
    color: "#f97316",
    desc: "Auksion qonuniy, lekin uni ko'rish, tushunish yoki bahslashish qiyin.",
    rules: [
      ["closed_auction", 30, "Yopiq auksion (is_closed=1)"],
      ["no_announcement", 20, "Natija e'lon qilinmaydi"],
      ["short_deadline", 15, "Taklif muddati < 7 kun"],
      ["short_deadline (urgent)", 25, "Taklif muddati < 3 kun"],
      ["low_visibility", 7, "<10 ko'rishlar + yopiq"],
    ],
  },
  {
    code: "B",
    name: "Kelishuv",
    full: "Collusion",
    color: "#a855f7",
    desc: "Sotuvchi va g'olib oldindan kelishib olganligi belgilari.",
    rules: [
      ["monopoly_seller", 30, "1000+ lot bir sotuvchida"],
      ["dominant_seller", 18, "300+ lot bir sotuvchida"],
      ["seller_closed_pattern", 15, "Sotuvchi 50%+ yopiq sotadi"],
    ],
  },
  {
    code: "C",
    name: "Auksion soxtaligi",
    full: "Bid-Rigging",
    color: "#ef4444",
    desc: "Auksion ko'rinishida bor, lekin g'olib oldindan aniq.",
    rules: [
      ["many_reauctions", 35, "15+ marta auksionga chiqarilgan"],
      ["repeat_auction", 22, "8-14 marta auksion"],
      ["reauction", 12, "5-7 marta auksion"],
      ["single_bidder", 25, "1 ishtirokchi"],
      ["combo_single_closed", 20, "Yopiq + 1 ishtirokchi (bonus)"],
      ["descending_auction", 10, "Teskari auksion"],
      ["physical_only", 12, "Cheklangan ishtirokchi turi"],
    ],
  },
  {
    code: "D",
    name: "Firibgarlik",
    full: "Fraud",
    color: "#eab308",
    desc: "Narx, baho yoki hujjat manipulatsiyasi.",
    rules: [
      ["appraisal_severe", 35, "Baholangan narxdan -70%+ past"],
      ["below_appraisal", 22, "Baholangan narxdan -50% past"],
      ["below_appraisal (mild)", 12, "Baholangan narxdan -30% past"],
      ["deeply_underpriced", 22, "Hudud medianidan -70% past"],
      ["underpriced", 14, "Hudud medianidan -50% past"],
      ["deep_discount", 20, "Sotuv 30%+ past"],
      ["long_installment", 8, "60+ oy bo'lib to'lash"],
      ["stuck_lot_pattern", 10, "Re-auction + dominant seller"],
    ],
  },
  {
    code: "E",
    name: "Past raqobat",
    full: "Low Competition",
    color: "#06b6d4",
    desc: "Bozor sun'iy ravishda cheklangan.",
    rules: [
      ["(C1) single_bidder", 25, "1 ishtirokchi (overlap)"],
      ["(B2) monopoly_seller", 30, "Hududdagi monopoly (overlap)"],
      ["regional_dominance", 18, "v1.1 — kelajakda"],
      ["threshold_avoidance", 25, "v2 — lot bo'lib chiqarish"],
    ],
  },
];

const SOURCES = [
  {
    title: "OECD Anti-Corruption and Integrity Outlook 2026",
    href: "https://www.oecd.org/en/publications/anti-corruption-and-integrity-outlook-2026_16708b78-en/full-report/component-14.html",
  },
  {
    title: "Open Contracting Partnership — Cardinal & Red Flags Methodology",
    href: "https://www.open-contracting.org/2024/06/12/cardinal-an-open-source-library-to-calculate-public-procurement-red-flags/",
  },
  {
    title: "Mihály Fazekas — Corruption Risk Index (Cambridge / ERCAS, 2015)",
    href: "https://www.govtransparency.eu/wp-content/uploads/2015/11/GTI_WP2015_2_Fazekas_Kocsis_151015.pdf",
  },
  {
    title: "World Bank — Warning Signs of Fraud and Corruption in Procurement",
    href: "https://documents1.worldbank.org/curated/en/223241573576857116/pdf/Warning-Signs-of-Fraud-and-Corruption-in-Procurement.pdf",
  },
  {
    title: "Transparency International EU — Integrity Watch Red Flags",
    href: "https://transparency.eu/integrity-watch-red-flags/",
  },
  {
    title: "Ukraine DOZORRO — Civic AI Procurement Monitoring",
    href: "https://ti-ukraine.org/en/news/dozorro-artificial-intelligence-to-find-violations-in-prozorro-how-it-works/",
  },
  {
    title: "Brazil ALICE — AI Risk Detection in Public Procurement",
    href: "https://kun.uz/en/news/2025/03/05/uzbekistan-to-use-ai-for-fraud-prevention-in-public-procurement",
  },
  {
    title: "UN Convention against Corruption (UNCAC) — Article 9",
    href: "https://www.unodc.org/unodc/en/treaties/CAC/",
  },
];

export default function MethodologyPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker">METODOLOGIYA · v1.1</div>
        <h1 className="headline mt-2 text-4xl text-white">
          5 ta xalqaro toifa, 18+ ta signal
        </h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          AuksionWatch xavf reytingi — <strong>OECD</strong> va{" "}
          <strong>Open Contracting Partnership</strong> tomonidan ishlab chiqilgan
          standart taksonomiyaga asoslangan. Mihály Fazekas (Cambridge) Corruption
          Risk Index metodologiyasi — eng kuchli signal sifatida{" "}
          <em>single bidding</em> indikatorini belgilaydi.
        </p>
        <p className="mt-3 text-sm text-[var(--fg-mute)]">
          Har lot uchun <strong>Risk Score 0–100</strong> hisoblanadi va 5 toifa
          bo&apos;yicha alohida sub-ball'lar beriladi. Risk score = Σ (rule.score ×
          rule.weight). 5 ta toifa: A — Low Transparency, B — Collusion, C —
          Bid-Rigging, D — Fraud, E — Low Competition.
        </p>
      </header>

      <section className="mt-10 space-y-8">
        {CATEGORIES.map((cat) => (
          <div key={cat.code} className="card">
            <div className="border-b border-[var(--line)] px-5 py-4 flex items-center gap-4">
              <div
                className="h-10 w-10 flex items-center justify-center font-bold mono text-lg"
                style={{
                  background: `${cat.color}22`,
                  color: cat.color,
                }}
              >
                {cat.code}
              </div>
              <div>
                <div className="kicker">{cat.full}</div>
                <div className="headline text-xl text-white">{cat.name}</div>
              </div>
            </div>
            <div className="px-5 py-4">
              <p className="text-sm text-zinc-300">{cat.desc}</p>
              <table className="tbl mt-4">
                <thead>
                  <tr>
                    <th>Rule</th>
                    <th className="text-right">Vazn</th>
                    <th>Tushuntirish</th>
                  </tr>
                </thead>
                <tbody>
                  {cat.rules.map(([rule, score, desc], i) => (
                    <tr key={i}>
                      <td className="mono text-xs text-zinc-300 whitespace-nowrap">
                        {rule}
                      </td>
                      <td className="mono tabnum text-right text-[var(--red)] whitespace-nowrap">
                        +{score}
                      </td>
                      <td className="text-sm text-zinc-400">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </section>

      <section className="mt-12 border-t border-[var(--line)] pt-8">
        <div className="kicker mb-3">XALQARO MANBALAR</div>
        <h2 className="headline text-2xl text-white mb-5">
          Akademik va institutsional asos
        </h2>
        <ul className="space-y-3">
          {SOURCES.map((s) => (
            <li key={s.href} className="flex items-baseline gap-3">
              <span className="text-[var(--fg-dim)] mono text-xs mt-0.5">→</span>
              <a
                href={s.href}
                target="_blank"
                rel="noreferrer"
                className="link-u text-zinc-200 hover:text-white"
              >
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-12 border-t border-[var(--line)] pt-8">
        <div className="kicker mb-3">OCHIQ ENG MUHIM</div>
        <h2 className="headline text-2xl text-white mb-3">
          Bizning ish butunlay ochiq
        </h2>
        <ul className="space-y-2 text-sm text-zinc-300">
          <li>
            <span className="text-[var(--red)] mono">→</span> <strong>Litsenziya:</strong>{" "}
            CC BY-SA 4.0 — har kim foydalanishi, o&apos;zgartirishi mumkin
          </li>
          <li>
            <span className="text-[var(--red)] mono">→</span>{" "}
            <strong>Ma&apos;lumot manbasi:</strong>{" "}
            <a
              href="https://e-auksion.uz"
              target="_blank"
              rel="noreferrer"
              className="link-u"
            >
              e-auksion.uz
            </a>
            {" "}(ochiq sitemap + rasmiy Excel hisobotlari)
          </li>
          <li>
            <span className="text-[var(--red)] mono">→</span> <strong>API:</strong>{" "}
            <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" className="link-u">
              Swagger hujjatlari
            </a>
          </li>
          <li>
            <span className="text-[var(--red)] mono">→</span>{" "}
            <strong>Eksport:</strong>{" "}
            <Link href="/api/export.csv" className="link-u">
              CSV
            </Link>
            {" "}/{" "}
            <Link href="/api/export.json" className="link-u">
              JSON
            </Link>
          </li>
        </ul>
      </section>

      <section className="mt-12 rounded border border-amber-900/40 bg-amber-950/20 p-5 text-sm text-zinc-300">
        <div className="kicker text-amber-400 mb-2">DISCLAIMER</div>
        <p>
          AuksionWatch — mustaqil monitoring tizimi. Aniqlangan signal'lar{" "}
          <strong>qonuniy aybdorlik degani emas</strong>, balki tahlil va
          tekshirish uchun ko&apos;rsatma. Har bir lot uchun manba e-auksion.uz
          sahifasiga link mavjud — siz har bir ma&apos;lumotni o&apos;zingiz
          tasdiqlashingiz mumkin. Ushbu loyiha hech qanday rasmiy davlat organi
          bilan bog&apos;liq emas.
        </p>
      </section>
    </main>
  );
}
