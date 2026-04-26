// Lots/Sellers ro'yxati uchun sahifalar boshqaruvi.
// Server-side rendered — Link orqali ?page=N parametrini almashtiradi va
// boshqa filtrlarni saqlaydi.
import Link from "next/link";

type Props = {
  total: number;        // umumiy natijalar soni (API count'dan)
  page: number;         // joriy sahifa (1-indexed)
  perPage: number;      // bir sahifadagi elementlar
  basePath: string;     // masalan "/lots"
  searchParams: Record<string, string | undefined>;  // saqlanishi kerak filtrlar
};

// "?page=N" qo'shib qolgan parametrlarni saqlaydigan URL yasash
function buildHref(
  basePath: string,
  searchParams: Record<string, string | undefined>,
  page: number
): string {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(searchParams)) {
    if (k === "page") continue;
    if (v) params.set(k, v);
  }
  if (page > 1) params.set("page", String(page));
  const qs = params.toString();
  return qs ? `${basePath}?${qs}` : basePath;
}

// Ko'rinadigan sahifa raqamlarini hisoblash: 1, ..., 4, 5, [6], 7, 8, ..., 99
function pageList(current: number, last: number): (number | "…")[] {
  if (last <= 7) return Array.from({ length: last }, (_, i) => i + 1);
  const set = new Set<number>([1, last, current, current - 1, current + 1]);
  if (current <= 3) {
    set.add(2);
    set.add(3);
    set.add(4);
  }
  if (current >= last - 2) {
    set.add(last - 1);
    set.add(last - 2);
    set.add(last - 3);
  }
  const sorted = [...set].filter((n) => n >= 1 && n <= last).sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  for (let i = 0; i < sorted.length; i++) {
    out.push(sorted[i]);
    if (i < sorted.length - 1 && sorted[i + 1] - sorted[i] > 1) out.push("…");
  }
  return out;
}

export function Pagination({
  total,
  page,
  perPage,
  basePath,
  searchParams,
}: Props) {
  const lastPage = Math.max(1, Math.ceil(total / perPage));
  if (lastPage <= 1) return null;

  const safePage = Math.min(Math.max(1, page), lastPage);
  const from = (safePage - 1) * perPage + 1;
  const to = Math.min(total, safePage * perPage);

  const pages = pageList(safePage, lastPage);

  return (
    <nav
      className="mt-6 flex flex-wrap items-center justify-between gap-3"
      aria-label="Sahifalar"
    >
      <div className="text-xs text-[var(--fg-mute)] mono">
        {from.toLocaleString()}–{to.toLocaleString()} /{" "}
        <strong className="text-[var(--fg)]">{total.toLocaleString()}</strong>
      </div>

      <div className="flex items-center gap-1">
        {/* Oldingi */}
        {safePage > 1 ? (
          <Link
            href={buildHref(basePath, searchParams, safePage - 1)}
            className="px-3 py-1.5 text-sm border border-[var(--line)] rounded hover:bg-[var(--primary-soft)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-colors"
            aria-label="Oldingi sahifa"
          >
            ← Oldingi
          </Link>
        ) : (
          <span className="px-3 py-1.5 text-sm border border-[var(--line)] rounded text-[var(--fg-dim)] cursor-not-allowed">
            ← Oldingi
          </span>
        )}

        {pages.map((p, i) =>
          p === "…" ? (
            <span
              key={`gap-${i}`}
              className="px-2 text-sm text-[var(--fg-dim)]"
            >
              …
            </span>
          ) : p === safePage ? (
            <span
              key={p}
              aria-current="page"
              className="px-3 py-1.5 text-sm border border-[var(--primary)] bg-[var(--primary)] text-white rounded mono font-bold"
            >
              {p}
            </span>
          ) : (
            <Link
              key={p}
              href={buildHref(basePath, searchParams, p)}
              className="px-3 py-1.5 text-sm border border-[var(--line)] rounded hover:bg-[var(--primary-soft)] hover:border-[var(--primary)] hover:text-[var(--primary)] mono transition-colors"
            >
              {p}
            </Link>
          )
        )}

        {/* Keyingi */}
        {safePage < lastPage ? (
          <Link
            href={buildHref(basePath, searchParams, safePage + 1)}
            className="px-3 py-1.5 text-sm border border-[var(--line)] rounded hover:bg-[var(--primary-soft)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-colors"
            aria-label="Keyingi sahifa"
          >
            Keyingi →
          </Link>
        ) : (
          <span className="px-3 py-1.5 text-sm border border-[var(--line)] rounded text-[var(--fg-dim)] cursor-not-allowed">
            Keyingi →
          </span>
        )}
      </div>
    </nav>
  );
}
