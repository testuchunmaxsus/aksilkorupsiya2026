"use client";
// "Bu lot bilan nima qilish kerak?" — har lot pastida ko'rinadigan harakat tugmalari.
// Foydalanuvchini "topdim, endi nima?" savolisiz qoldirmaslik uchun.
import type { Lot } from "@/lib/api";

export function ActionBox({ lot }: { lot: Lot }) {
  // Joriy sahifa URL'i — ulashish uchun
  const shareUrl = typeof window !== "undefined" ? window.location.href : "";

  // Web Share API (mobile) yoki fallback — link nusxalash
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `AuksionWatch — Lot #${lot.id}`,
          text: lot.title || "Shubhali lot",
          url: shareUrl,
        });
      } catch {
        /* foydalanuvchi bekor qildi */
      }
    } else {
      navigator.clipboard.writeText(shareUrl);
      alert("Sahifa havolasi nusxalandi");
    }
  };

  // Anti-corruption agency formasi uchun pre-fill matni
  const reportText = `Salom! Quyidagi e-auksion loti shubhali ko'rinmoqda:\n\nLot: #${lot.id}\nManba: ${lot.url}\nAuksionWatch hisoboti: ${shareUrl}\n\nTekshirib chiqishingizni so'rayman.`;
  const reportUrl = `mailto:info@anticorruption.uz?subject=${encodeURIComponent(
    `Shubhali lot: #${lot.id}`,
  )}&body=${encodeURIComponent(reportText)}`;

  // decisions.esud.uz da sotuvchi nomi bilan qidiruv
  const courtUrl = lot.seller_name
    ? `https://decisions.esud.uz/search?q=${encodeURIComponent(lot.seller_name)}`
    : "https://decisions.esud.uz";

  return (
    <section className="card p-5 md:p-6">
      <div className="kicker mb-4">Bu lot uchun nima qilishim mumkin?</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          onClick={handleShare}
          className="action-tile group"
          type="button"
        >
          <span className="action-icon">📤</span>
          <div className="text-left">
            <div className="font-semibold text-[var(--fg)]">Ulashish</div>
            <div className="text-xs text-[var(--fg-mute)] mt-0.5">
              Tanish, hamkasb yoki jurnalistga
            </div>
          </div>
        </button>

        <button
          onClick={() => window.print()}
          className="action-tile group"
          type="button"
        >
          <span className="action-icon">📄</span>
          <div className="text-left">
            <div className="font-semibold text-[var(--fg)]">PDF hisobot</div>
            <div className="text-xs text-[var(--fg-mute)] mt-0.5">
              A4 — sud yoki gazeta uchun
            </div>
          </div>
        </button>

        <a href={reportUrl} className="action-tile group">
          <span className="action-icon">🚨</span>
          <div className="text-left">
            <div className="font-semibold text-[var(--fg)]">
              Aksilkorrupsiya'ga signal
            </div>
            <div className="text-xs text-[var(--fg-mute)] mt-0.5">
              anticorruption.uz — rasmiy organ
            </div>
          </div>
        </a>

        <a
          href={courtUrl}
          target="_blank"
          rel="noreferrer"
          className="action-tile group"
        >
          <span className="action-icon">⚖️</span>
          <div className="text-left">
            <div className="font-semibold text-[var(--fg)]">
              Sud ishlarini tekshirish
            </div>
            <div className="text-xs text-[var(--fg-mute)] mt-0.5">
              decisions.esud.uz — sotuvchi tarixi
            </div>
          </div>
        </a>
      </div>

      <style jsx>{`
        .action-tile {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 14px 16px;
          background: var(--bg-soft);
          border: 1px solid var(--line);
          border-radius: 12px;
          text-align: left;
          transition: all 150ms ease;
          cursor: pointer;
          width: 100%;
        }
        .action-tile:hover {
          border-color: var(--primary);
          background: var(--primary-soft);
          transform: translateY(-1px);
        }
        .action-icon {
          flex-shrink: 0;
          font-size: 28px;
          line-height: 1;
        }
      `}</style>
    </section>
  );
}
