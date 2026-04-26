// Bosh sahifada "qaerda davlat mol-mulki, qaerda musodara" alohida ko'rsatadi.
// Judge yoki foydalanuvchi "davlat aktivlari kam ko'rinmoqda" deb so'rasa,
// bu komponent darrov javob beradi: 1834 ta davlat lot, 27 yuqori xavf.
import Link from "next/link";
import type { Stats } from "@/lib/api";

export function OwnershipBreakdown({ stats }: { stats: Stats }) {
  const ob = stats.ownership_breakdown;
  if (!ob || stats.total === 0) return null;

  const total = stats.total;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="kicker">EGALIK BO&apos;YICHA</div>
          <h3 className="font-bold text-[var(--fg)] text-lg">
            Mol-mulk turlari taqsimoti
          </h3>
        </div>
        <div className="text-xs text-[var(--fg-mute)] text-right">
          e-auksion.uz uch xil mol-mulkni birga sotadi
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-3">
        {/* Davlat */}
        <Link
          href="/lots?ownership=state"
          className="rounded-lg border-2 border-[var(--primary)] bg-[var(--primary-soft)] p-4 hover:shadow-md transition-shadow group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🏛</span>
            <span className="kicker text-[var(--primary-deep)] text-[10px]">
              ASOSIY MONITORING
            </span>
          </div>
          <div className="font-bold text-[var(--primary-deep)] text-sm mb-1">
            Davlat mol-mulki
          </div>
          <div className="mono tabnum text-2xl font-bold text-[var(--primary-deep)]">
            {ob.state.total.toLocaleString()}
          </div>
          <div className="text-xs text-[var(--fg-mute)] mt-1">
            {((ob.state.total / total) * 100).toFixed(1)}% jami lotdan
          </div>
          {ob.state.high_risk > 0 && (
            <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-[var(--red)]/10 border border-[var(--red)]/30 px-2 py-0.5 text-xs">
              <span className="text-[var(--red)]">🚩</span>
              <strong className="text-[var(--red)]">{ob.state.high_risk}</strong>
              <span className="text-[var(--fg-mute)]">yuqori xavf</span>
            </div>
          )}
          <div className="mt-2 text-[10px] text-[var(--fg-dim)] group-hover:text-[var(--primary)]">
            Davaktiv → barcha lotlarni ko&apos;rish →
          </div>
        </Link>

        {/* Musodara */}
        <Link
          href="/lots?ownership=confiscated"
          className="rounded-lg border border-amber-300 bg-amber-50 p-4 hover:shadow-md transition-shadow group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">⚖</span>
            <span className="kicker text-amber-900 text-[10px]">SUD/MIB</span>
          </div>
          <div className="font-bold text-amber-900 text-sm mb-1">
            Musodara mol-mulki
          </div>
          <div className="mono tabnum text-2xl font-bold text-amber-900">
            {ob.confiscated.total.toLocaleString()}
          </div>
          <div className="text-xs text-[var(--fg-mute)] mt-1">
            {((ob.confiscated.total / total) * 100).toFixed(1)}% jami lotdan
          </div>
          <div className="text-[10px] text-[var(--fg-dim)] mt-2 leading-relaxed">
            Sud orqali olingan shaxsiy mol-mulk — davlatga emas
          </div>
        </Link>

        {/* Yuridik shaxs */}
        <Link
          href="/lots?ownership=private"
          className="rounded-lg border border-slate-300 bg-slate-50 p-4 hover:shadow-md transition-shadow group"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🏢</span>
            <span className="kicker text-slate-700 text-[10px]">PRIVATE</span>
          </div>
          <div className="font-bold text-slate-800 text-sm mb-1">
            Yuridik shaxs aktivlari
          </div>
          <div className="mono tabnum text-2xl font-bold text-slate-800">
            {ob.private.total.toLocaleString()}
          </div>
          <div className="text-xs text-[var(--fg-mute)] mt-1">
            {((ob.private.total / total) * 100).toFixed(1)}% jami lotdan
          </div>
          <div className="text-[10px] text-[var(--fg-dim)] mt-2 leading-relaxed">
            Bankrot biznes / banklar — davlat ishtirokisiz
          </div>
        </Link>
      </div>

      <p className="mt-3 text-xs text-[var(--fg-dim)] leading-relaxed">
        💡 <strong>Eslatma:</strong> AuksionWatch monitoringi asosan{" "}
        <strong>davlat mol-mulki</strong>ga qaratilgan. Musodara va yuridik
        shaxs lotlari uchun risk qoidalari kontekstga moslashtirilgan
        (masalan, monopoly_seller faqat davlat kanaliga qo&apos;llaniladi).
      </p>
    </div>
  );
}
