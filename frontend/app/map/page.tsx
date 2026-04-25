import { api, REGION_NAMES, formatUZS } from "@/lib/api";
import { LotMap } from "@/components/LotMap";

export const dynamic = "force-dynamic";

export default async function MapPage() {
  const [markers, stats] = await Promise.all([
    api.markers().catch(() => []),
    api.stats().catch(() => null),
  ]);
  const high = markers.filter((m) => m.level === "high").length;
  const medium = markers.filter((m) => m.level === "medium").length;
  const low = markers.length - high - medium;

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker">GEO · INTERACTIVE</div>
        <h1 className="headline mt-2 text-4xl text-white">Lotlar xaritasi</h1>
        <p className="mt-2 text-sm text-zinc-400 max-w-2xl">
          O&apos;zbekiston bo&apos;yicha barcha auksion lotlarining geografik
          taqsimoti. Marker rangi xavf darajasini bildiradi. Eng katta qizil
          nuqtalar — eng shubhali sxemalar.
        </p>
      </header>

      <div className="mt-6 grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <LotMap markers={markers} />
        </div>
        <aside className="space-y-4">
          <div className="card">
            <div className="border-b border-[var(--line)] px-4 py-2.5">
              <div className="kicker">XULOSA</div>
            </div>
            <div className="divide-y divide-[var(--line-soft)]">
              <Row dot="var(--red)" label="Yuqori xavf" value={high} />
              <Row dot="var(--amber)" label="O'rta xavf" value={medium} />
              <Row dot="var(--emerald)" label="Oz xavf" value={low} />
              <Row label="JAMI" value={markers.length} bold />
            </div>
          </div>

          {stats && (
            <div className="card">
              <div className="border-b border-[var(--line)] px-4 py-2.5">
                <div className="kicker">XAVFLI HUDUDLAR · TOP 5</div>
              </div>
              <ul className="divide-y divide-[var(--line-soft)]">
                {stats.high_risk_by_region
                  .sort((a, b) => b.high_count - a.high_count)
                  .slice(0, 5)
                  .map((r, i) => (
                    <li
                      key={r.region}
                      className="flex items-center justify-between px-4 py-2.5"
                    >
                      <div className="flex items-center gap-3">
                        <span className="mono text-xs text-[var(--fg-dim)] tabnum w-5">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <span className="text-sm text-zinc-200">
                          {REGION_NAMES[r.region] || r.region}
                        </span>
                      </div>
                      <span className="mono tabnum text-[var(--red)] font-bold">
                        {r.high_count}
                      </span>
                    </li>
                  ))}
              </ul>
            </div>
          )}

          <div className="card p-4 text-xs text-[var(--fg-mute)] leading-relaxed">
            <div className="kicker text-[var(--fg-dim)] mb-2">METODOLOGIYA</div>
            Geo-koordinatalar viloyat markazi bo&apos;yicha jitter bilan
            taqsimlangan, chunki e-auksion.uz lot-darajasidagi koordinatalarni
            ochiq bermaydi. Keyingi versiyada manzilni Nominatim orqali to&apos;liq
            geokod qilamiz.
          </div>
        </aside>
      </div>
    </main>
  );
}

function Row({
  dot,
  label,
  value,
  bold,
}: {
  dot?: string;
  label: string;
  value: number;
  bold?: boolean;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5">
      <div className="flex items-center gap-2.5">
        {dot ? (
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: dot }}
          />
        ) : (
          <span className="w-2.5" />
        )}
        <span className={`text-sm ${bold ? "kicker text-white" : "text-zinc-300"}`}>
          {label}
        </span>
      </div>
      <span
        className={`mono tabnum ${
          bold ? "headline text-2xl text-white" : "text-zinc-200"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
