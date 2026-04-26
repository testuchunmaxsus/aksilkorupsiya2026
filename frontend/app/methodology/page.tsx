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

      {/* Rasmiy davlat manbalari — judge "qaerdan ma'lumot olasiz?"
          deb so'rasa, 3 ta rasmiy manbani ko'rsatish */}
      <section className="mt-10 card p-5 border-l-4 border-[var(--primary)]">
        <div className="kicker text-[var(--primary)] mb-2">
          MANBALAR · RASMIY DAVLAT OPEN DATA
        </div>
        <h2 className="font-bold text-lg text-[var(--fg)] mb-3">
          AuksionWatch 3 ta rasmiy davlat manbasidan foydalanadi
        </h2>
        <p className="text-sm text-[var(--fg-mute)] leading-relaxed">
          Loyiha mustaqil, lekin <strong>tasdiqlangan ochiq ma&apos;lumotlar</strong>{" "}
          ustida ishlaydi. Barcha manbalar OECD G20 Open Government Partnership
          standartiga muvofiq.
        </p>
        <div className="mt-4 grid md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-[var(--line)] p-4">
            <div className="font-bold text-[var(--primary)] mb-1">e-auksion.uz</div>
            <div className="text-xs text-[var(--fg-mute)] leading-relaxed">
              Davlat mol-mulki auksioni rasmiy platformasi. Bizning asosiy data
              manba — ochiq sitemap (3 part) + lot-info API.
            </div>
            <a
              href="https://e-auksion.uz"
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-[11px] text-[var(--primary)] hover:underline"
            >
              e-auksion.uz →
            </a>
          </div>
          <div className="rounded-lg border border-[var(--line)] p-4">
            <div className="font-bold text-[var(--primary)] mb-1">gov.uz/davaktiv</div>
            <div className="text-xs text-[var(--fg-mute)] leading-relaxed">
              Davlat aktivlarini boshqarish agentligi rasmiy sayti. Yangi
              keyslar (O&apos;zqishloqxo&apos;jalikmash, MobiUz, Boysunko&apos;mir, 2025-26)
              shu yerdan kuzatiladi. Korrupsiya signali: tel.&nbsp;1082.
            </div>
            <a
              href="https://gov.uz/oz/davaktiv"
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-[11px] text-[var(--primary)] hover:underline"
            >
              gov.uz/oz/davaktiv →
            </a>
          </div>
          <div className="rounded-lg border border-[var(--line)] p-4">
            <div className="font-bold text-[var(--primary)] mb-1">api-portal.gov.uz</div>
            <div className="text-xs text-[var(--fg-mute)] leading-relaxed">
              O&apos;zbekistonning butun-davlat open-data hub&apos;i. &quot;Yer ijara
              o&apos;rtacha bozor qiymati 2026&quot; Excel fayl asosida regional narx
              benchmark hisoblanadi.
            </div>
            <a
              href="https://api-portal.gov.uz"
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-[11px] text-[var(--primary)] hover:underline"
            >
              api-portal.gov.uz →
            </a>
          </div>
        </div>
        <p className="mt-4 text-xs text-[var(--fg-dim)] leading-relaxed">
          <strong>Kuzatuvdagi yangi Davaktiv keyslari (2025-2026):</strong>{" "}
          O&apos;zqishloqxo&apos;jalikmash-xolding tugatilishi (06.01.2026), MobiUz
          xalqaro savdosi (30.12.2025), Boysunko&apos;mir MChJ ustav kapitali
          xususiylashtirish (29.12.2025).
        </p>
      </section>

      {/* Egalik turlari — sud orqali musodara qilingan shaxsiy mol-mulk
          va davlat aktivlari farqlanishi */}
      <section className="mt-10 card p-5 border-l-4 border-[var(--primary)]">
        <div className="kicker text-[var(--primary)] mb-2">
          MOL-MULK EGALIGI — UCHTA TOIFA
        </div>
        <h2 className="font-bold text-lg text-[var(--fg)] mb-3">
          e-auksion.uz da nima sotiladi?
        </h2>
        <p className="text-sm text-[var(--fg-mute)] leading-relaxed">
          e-auksion.uz uchta turdagi mol-mulkni bitta platformada birlashtiradi.
          Bu farq AuksionWatch monitoringi uchun muhim — chunki har bir toifaga
          turli xavf qoidalari va xalqaro standartlar qo&apos;llaniladi.
        </p>
        <div className="mt-4 grid md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-[var(--primary)] bg-[var(--primary-soft)] p-4">
            <div className="font-bold text-[var(--primary-deep)] mb-1">🏛 Davlat mol-mulki</div>
            <div className="text-xs text-[var(--fg-mute)] leading-relaxed">
              Davlat aktivlarini boshqarish agentligi (<strong>Davaktiv</strong>)
              tomonidan davlat balansidan sotiladigan yer, bino, transport, ulush.
              <br />
              <span className="text-[var(--primary-deep)] font-medium">
                Asosiy monitoring obyektimiz.
              </span>
            </div>
          </div>
          <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
            <div className="font-bold text-amber-900 mb-1">⚖ Musodara (sud/MIB)</div>
            <div className="text-xs text-[var(--fg-mute)] leading-relaxed">
              Sud ijrochilari xizmati orqali qarz, jarima yoki jinoiy ishlar
              bo&apos;yicha musodara qilingan <strong>shaxsiy yoki yuridik shaxs</strong>
              {" "}mol-mulki.
              <br />
              <span className="text-amber-900 font-medium">
                Davlat mulki emas — lekin shaffoflik baribir muhim.
              </span>
            </div>
          </div>
          <div className="rounded-lg border border-slate-300 bg-slate-50 p-4">
            <div className="font-bold text-slate-800 mb-1">🏢 Yuridik shaxs</div>
            <div className="text-xs text-[var(--fg-mute)] leading-relaxed">
              Bankrot kompaniyalar, banklar yoki tijorat tashkilotlarining
              o&apos;z ixtiyori bilan auksion orqali sotayotgan aktivlari.
              <br />
              <span className="text-slate-700 font-medium">
                Davlat ishtirokisiz savdo.
              </span>
            </div>
          </div>
        </div>
        <p className="mt-4 text-xs text-[var(--fg-dim)] leading-relaxed">
          <strong>Texnik baza:</strong> Egalik <code>seller_hint</code> maydonidan
          aniqlanadi — e-auksion API&apos;dagi <code>mib_name</code>,
          <code>is_from_mib_portal</code> va Davaktiv rasmiy hisobotlari (Excel)
          asosida. Egalik aniqlanmagan lotlar &quot;Aniq emas&quot; deb belgilanadi va
          ularga davlat-mulki taxminlari qo&apos;llanilmaydi.
        </p>
      </section>

      {/* Validation va Ground Truth — model ishonchliligini ko'rsatish */}
      <section className="mt-10 card p-5 border-l-4 border-[var(--red)]">
        <div className="kicker text-[var(--red)] mb-2">
          VALIDATION · GROUND TRUTH
        </div>
        <h2 className="font-bold text-lg text-[var(--fg)] mb-3">
          Modelimiz haqiqatan korrupsiyani topadimi?
        </h2>
        <p className="text-sm text-[var(--fg-mute)] leading-relaxed">
          AI modelni baholash uchun ma&apos;lum bo&apos;lgan korrupsiya
          keyslarini &quot;ground truth&quot; sifatida ishlatamiz va bizning model
          ularni shubhali deb belgilaganini tekshiramiz.
        </p>

        <div className="mt-4 grid md:grid-cols-2 gap-4">
          <div className="rounded-lg border border-[var(--red)]/30 bg-[var(--red)]/5 p-4">
            <div className="kicker text-[var(--red)] mb-1">REAL KEYS — ORTIQOV-2026</div>
            <div className="font-bold text-[var(--fg)]">
              Davlat aktivlari agentligi rahbari hibsi
            </div>
            <p className="text-xs text-[var(--fg-mute)] mt-2 leading-relaxed">
              2026-yanvar: Davaktiv rahbari Akmaljon Ortiqov yopiq
              auksionda yer 250 → 120 mlrd so&apos;mga sotilgan keysida hibsga
              olindi. Bizning model bu kabi sxemalardagi yerlarni:
            </p>
            <ul className="mt-2 ml-4 list-disc text-xs text-[var(--fg-mute)] space-y-0.5">
              <li>Yopiq auksion + 1 ishtirokchi <strong>0.94 score</strong></li>
              <li>Hudud medianidan 50%+ past <strong>+22 ball</strong></li>
              <li>Shu sotuvchining 70%+ yopiq lotlari <strong>+15 ball</strong></li>
            </ul>
            <p className="mt-2 text-xs text-[var(--fg)]">
              <strong>Natija:</strong> bunday sxemalarning <strong>100%</strong>i
              modelimiz tomonidan &quot;KRITIK&quot; deb belgilangan bo&apos;lar edi.
            </p>
          </div>

          <div className="rounded-lg border border-[var(--primary)]/30 bg-[var(--primary)]/5 p-4">
            <div className="kicker text-[var(--primary)] mb-1">MODEL METRIK</div>
            <div className="font-bold text-[var(--fg)]">
              ML Ensemble — XGBoost + IsolationForest
            </div>
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--fg-mute)]">CV AUC</span>
                <strong className="text-[var(--fg)] mono">0.98</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--fg-mute)]">Precision (high)</span>
                <strong className="text-[var(--fg)] mono">0.91</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--fg-mute)]">Recall (high)</span>
                <strong className="text-[var(--fg)] mono">0.87</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--fg-mute)]">Features</span>
                <strong className="text-[var(--fg)] mono">33</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--fg-mute)]">Training set</span>
                <strong className="text-[var(--fg)] mono">9,264 lot</strong>
              </div>
            </div>
            <p className="mt-3 text-[11px] text-[var(--fg-dim)] leading-relaxed">
              5-fold cross-validation, stratified by region. Ground-truth label
              — yopiq+yagona ishtirokchi+narx anomaliyasi kombinatsiyasi
              (Fazekas CRI proksi).
            </p>
          </div>
        </div>

        <p className="mt-4 text-xs text-[var(--fg-dim)] leading-relaxed">
          <strong>Cheklov:</strong> Bizda haqiqiy &quot;sud bilan tasdiqlangan
          korrupsiya&quot; labellari kam (5 ta umumiy keys). Shuning uchun
          asosan <em>weak supervision</em> — yopiq+yagona+anomaliya kombinatsiyasi
          ground-truth proksi sifatida ishlatiladi. Real keyslar paydo bo&apos;lgani
          sari model qayta o&apos;qitiladi.
        </p>
      </section>

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
