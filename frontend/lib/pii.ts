// PII (shaxsiy ma'lumotlar) maskalash helperlari.
// Davaktiv hisobotlari rasmiy ochiq ma'lumot hisoblanadi (sotuvchi tashkilot
// nomlari shaffoflik talabi bilan oshkor qilinadi). Lekin musodara MIB lotlarida
// sotuvchi sifatida shaxsiy fuqaro ismi bo'lishi mumkin — bunday hollarda
// "Last name + boshlang'ich harf" formatiga keltiramiz.
//
// Standart: GDPR Art.5(1)(c) "data minimisation" + UZ shaxsiy ma'lumotlar qonuni.

const ORG_KEYWORDS = [
  "MCHJ",
  "AJ",
  "OOO",
  "ОАО",
  "BANK",
  "БАНК",
  "DAVAKTIV",
  "ДАВАКТИВ",
  "AGENTLIGI",
  "TASHKILOTI",
  "BOSHQARMASI",
  "DEPARTAMENTI",
  "VAZIRLIK",
  "INSPEKSIYA",
  "MIB",
  "МИБ",
  "SUD",
  "СУД",
  "QO'MITASI",
];

// Tashkilot deb taxmin qilish — yuqoridagi kalit so'zlardan biri bor bo'lsa
function looksLikeOrganization(name: string): boolean {
  const upper = name.toUpperCase();
  return ORG_KEYWORDS.some((kw) => upper.includes(kw));
}

/**
 * Shaxsiy fuqaro ismini PII xavfsizlik uchun maskalaydi.
 *
 * Kirish: "Ortiqov Akmaljon Tursunovich"
 * Chiqish: "Ortiqov A. T."
 *
 * Tashkilot bo'lsa — to'liq qaytaradi (ochiq ma'lumot).
 *
 * @param sellerHint  agar "davaktiv"/"state"/"gov" — shaffoflik talabi, maskalanmaydi
 * @param sellerName  to'liq nom (FIO yoki tashkilot nomi)
 */
export function maskSellerName(
  sellerName: string | null | undefined,
  sellerHint: string | null | undefined
): string {
  if (!sellerName) return "—";
  const trimmed = sellerName.trim();

  // Davlat kanali — shaffoflik talabi, to'liq nom ko'rinadi
  const hint = (sellerHint || "").toLowerCase();
  if (hint === "davaktiv" || hint === "state" || hint === "gov") {
    return trimmed;
  }

  // Tashkilot — qonuniy yuridik shaxs, to'liq nom ko'rinadi
  if (looksLikeOrganization(trimmed)) {
    return trimmed;
  }

  // Shaxsiy fuqaro — familiya + boshlang'ich harf'lar
  const parts = trimmed.split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "—";
  if (parts.length === 1) return parts[0];
  const lastName = parts[0];
  const initials = parts.slice(1).map((p) => p[0].toUpperCase() + ".");
  return `${lastName} ${initials.join(" ")}`;
}

/**
 * Telefon raqamini maskalaydi: +998 90 *** ** 12
 */
export function maskPhone(phone: string | null | undefined): string {
  if (!phone) return "—";
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 9) return "—";
  const last2 = digits.slice(-2);
  const code = digits.startsWith("998") ? "+998" : "+998";
  const op = digits.length >= 12 ? digits.slice(3, 5) : digits.slice(0, 2);
  return `${code} ${op} *** ** ${last2}`;
}

/**
 * Manzilni qisman maskalaydi — uy raqami va kvartira yashiriladi.
 * "Toshkent, Yunusobod, Karasu-2, 14-uy, 32-xonadon"
 *  → "Toshkent, Yunusobod, Karasu-2"
 */
export function maskAddress(addr: string | null | undefined): string {
  if (!addr) return "—";
  // "uy", "xonadon", uy raqami (12, 14a, 14-uy) — kesib tashlaymiz
  const parts = addr.split(/[,;]/).map((p) => p.trim());
  const filtered = parts.filter(
    (p) =>
      !/uy|xonadon|kv\.?|кв\.?|дом|квартира/i.test(p) &&
      !/^\d+[a-zа-я]?(-uy)?$/i.test(p)
  );
  return filtered.join(", ");
}
