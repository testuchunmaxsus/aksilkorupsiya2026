// Mol-mulkning kim egaligida ekanini aniq ko'rsatadi.
// e-auksion.uz uch xil mol-mulkni sotadi:
//   1) "davaktiv" — Davlat aktivlari (haqiqiy davlat mol-mulki)
//   2) "court" / "mib" — sud ijrochilari orqali musodara qilingan SHAXSIY mol-mulk
//   3) "individual" / boshqa — yuridik shaxslar, bankrot biznes, h.k.
// Bu farq juda muhim: AuksionWatch monitoringi asosan davlat aktivlariga qaratilgan.

export type OwnershipKind =
  | "state"        // Davlat mol-mulki (Davaktiv)
  | "confiscated"  // Musodara (sud / MIB)
  | "private"      // Yuridik shaxs / shaxsiy
  | "unknown";

export function classifyOwnership(seller_hint: string | null | undefined): OwnershipKind {
  if (!seller_hint) return "unknown";
  const h = seller_hint.toLowerCase();
  if (h === "davaktiv" || h === "state" || h === "gov") return "state";
  if (h === "court" || h === "mib" || h === "bank") return "confiscated";
  if (h === "individual" || h === "private") return "private";
  return "unknown";
}

const META: Record<OwnershipKind, { label: string; emoji: string; color: string; tooltip: string }> = {
  state: {
    label: "Davlat mol-mulki",
    emoji: "🏛",
    color: "bg-[var(--primary-soft)] text-[var(--primary-deep)] border-[var(--primary)]",
    tooltip: "Davlat aktivlarini boshqarish agentligi (Davaktiv) tomonidan sotilmoqda",
  },
  confiscated: {
    label: "Musodara (sud/MIB)",
    emoji: "⚖",
    color: "bg-amber-50 text-amber-900 border-amber-300",
    tooltip:
      "Sud ijrochilari xizmati (MIB) orqali sotilayotgan musodara mol-mulk. " +
      "Asl egasi shaxsiy yoki yuridik shaxs bo'lishi mumkin.",
  },
  private: {
    label: "Yuridik shaxs",
    emoji: "🏢",
    color: "bg-slate-50 text-slate-800 border-slate-300",
    tooltip: "Bankrot yoki yuridik shaxs aktivlari — bu davlat mol-mulki emas",
  },
  unknown: {
    label: "Egalik aniq emas",
    emoji: "❔",
    color: "bg-slate-50 text-slate-500 border-slate-200",
    tooltip: "Sotuvchi turi aniqlanmadi",
  },
};

export function OwnershipBadge({
  seller_hint,
  size = "md",
}: {
  seller_hint: string | null | undefined;
  size?: "sm" | "md";
}) {
  const kind = classifyOwnership(seller_hint);
  const m = META[kind];
  const sizeCls = size === "sm" ? "text-[11px] px-2 py-0.5" : "text-xs px-2.5 py-1";
  return (
    <span
      title={m.tooltip}
      className={`inline-flex items-center gap-1.5 rounded-full border ${m.color} ${sizeCls} font-medium`}
    >
      <span aria-hidden>{m.emoji}</span>
      <span>{m.label}</span>
    </span>
  );
}
