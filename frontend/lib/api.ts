// Backend API'ning bazaviy URL'i — production'da Railway domain, develop'da localhost
export const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Risk engine'dan kelgan asosiy flag obyekti
export type Flag = {
  type: string;     // "single_bidder", "monopoly_seller", ...
  score: number;    // bu flag uchun ball
  title: string;    // foydalanuvchi ko'radigan sarlavha
  desc: string;     // tushuntirish matni
};

// PEP (mansabdor) match natijasi — FATF R12 bo'yicha
export type PEPMatch = {
  pep_id: string;
  pep_name: string;
  match_type: "exact" | "alias" | "fuzzy" | "family_lastname";
  similarity: number;     // 0-1
  category?: string;
  case_url?: string;      // tashqi keys URL'i
  case_summary?: string;  // qisqa keys tavsifi
};

// Flag + qo'shimcha provenance ma'lumotlar (UI'da explainability uchun)
export type Flag2 = Flag & {
  category?: "A" | "B" | "C" | "D" | "E";  // OECD toifasi
  ref?: string;            // standart manba (masalan "Fazekas CRI · OCDS R001")
  ref_url?: string;        // URL — bosib o'tish mumkin
  formula?: string;        // matematik shart
  fields?: string[];       // ishlatilgan e-auksion maydonlari
  weight?: number;
  weighted_score?: number; // score × weight
  pep?: PEPMatch;          // faqat PEP flag'lar uchun
};

// 5 OECD toifasi bo'yicha sub-ballar
export type Categories = { A: number; B: number; C: number; D: number; E: number };

// Toifa kodlari → o'zbekcha nom (UI'da ko'rsatish uchun)
export const CATEGORY_LABEL: Record<string, { name: string; full: string }> = {
  A: { name: "Past shaffoflik", full: "A. Low Transparency" },
  B: { name: "Kelishuv", full: "B. Collusion" },
  C: { name: "Auksion soxtaligi", full: "C. Bid-Rigging" },
  D: { name: "Firibgarlik", full: "D. Fraud" },
  E: { name: "Past raqobat", full: "E. Low Competition" },
};

export type Lot = {
  id: number;
  url: string;
  title: string | null;
  lot_type: string | null;
  lot_type_specific: string | null;
  address: string | null;
  region: string | null;
  district: string | null;
  start_price: number | null;
  sold_price: number | null;
  appraised_price: number | null;
  deposit: number | null;
  step_price: number | null;
  installment_months: number | null;
  auction_method: string | null;
  auction_style: string | null;
  auction_type: "open" | "closed";
  start_time: string | null;
  deadline: string | null;
  end_time: string | null;
  status: string | null;
  views: number | null;
  bidders_count: number | null;
  times_auctioned: number | null;
  seller_hint: string | null;
  seller_name: string | null;
  seller_id: number | null;
  geo_lat: number | null;
  geo_lon: number | null;
  is_descending: boolean | null;
  risk_score: number;
  risk_level: "low" | "medium" | "high";
  ai_summary: string | null;
  flags: Flag2[] | null;
  categories: Categories | null;
  ml_score: number | null;
  ml_level: string | null;
  ml_reason: string | null;
  ml_xgb_prob: number | null;
  ml_iso_score: number | null;
  scraped_at?: string | null;
};

export type Stats = {
  total: number;
  high_risk: number;
  medium_risk: number;
  closed_auctions: number;
  total_value_uzs: number;
  high_risk_value_uzs: number;
  by_region: { region: string; count: number }[];
  high_risk_by_region: { region: string; high_count: number }[];
  categories?: { code: string; lots_with_signal: number; avg_score: number }[];
  distribution?: {
    high: { count: number; pct: number };
    medium: { count: number; pct: number };
    low: { count: number; pct: number };
  };
};

export type SellerRow = {
  seller_id: number;
  seller_name: string | null;
  region: string | null;
  seller_hint: string | null;
  total_lots: number;
  closed_count: number;
  high_risk_count: number;
  medium_risk_count: number;
  avg_risk_score: number;
  total_value_uzs: number;
  closed_pct: number;
  high_risk_pct: number;
};

export type MapMarker = {
  id: number;
  lat: number;
  lon: number;
  risk: number;
  level: "low" | "medium" | "high";
  title: string;
  region: string | null;
};

// Generic fetch wrapper — JSON qaytaradi, HTTP xato bo'lsa exception ko'taradi
// cache: "no-store" — Next.js caching'ni o'chiradi (har request real-vaqt)
async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`API ${path} ${r.status}`);
  return r.json();
}

// Barcha API endpoint'lari uchun typed klient
export const api = {
  stats: () => get<Stats>("/api/stats"),
  lots: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))
    ).toString();
    return get<{ count: number; items: Lot[]; limit?: number; offset?: number }>(
      `/api/lots${qs ? `?${qs}` : ""}`
    );
  },
  lot: (id: number) => get<{ lot: Lot; related: Lot[] }>(`/api/lots/${id}`),
  redFlagsToday: (limit = 10) => get<{ items: Lot[] }>(`/api/red-flags/today?limit=${limit}`),
  markers: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))
    ).toString();
    return get<MapMarker[]>(`/api/map/markers${qs ? `?${qs}` : ""}`);
  },
  firm: (sellerHint: string) =>
    get<{
      seller_hint: string;
      total_lots: number;
      closed_pct: number;
      high_risk_count: number;
      items: Lot[];
    }>(`/api/firms/${encodeURIComponent(sellerHint)}`),
  sellers: (limit = 20, ownership?: string) =>
    get<{ items: SellerRow[] }>(
      `/api/sellers?limit=${limit}${ownership ? `&ownership=${ownership}` : ""}`
    ),
  timeline: () =>
    get<{
      series: {
        month: string;
        total: number;
        high: number;
        medium: number;
        closed: number;
        value: number;
      }[];
    }>("/api/stats/timeline"),
  network: (top = 50) =>
    get<{
      nodes: { id: string; type: string; label: string; value: number; risk?: number }[];
      edges: { source: string; target: string; value: number }[];
    }>(`/api/network?top=${top}`),
  seller: (sellerId: number) =>
    get<
      SellerRow & {
        total_value_uzs: number;
        items: Lot[];
      }
    >(`/api/sellers/${sellerId}`),
};

export const REGION_NAMES: Record<string, string> = {
  "UZ-TK": "Toshkent shahri",
  "UZ-TO": "Toshkent viloyati",
  "UZ-AN": "Andijon",
  "UZ-BU": "Buxoro",
  "UZ-FA": "Farg'ona",
  "UZ-JI": "Jizzax",
  "UZ-XO": "Xorazm",
  "UZ-NG": "Namangan",
  "UZ-NW": "Navoiy",
  "UZ-QA": "Qashqadaryo",
  "UZ-SA": "Samarqand",
  "UZ-SI": "Sirdaryo",
  "UZ-SU": "Surxondaryo",
  "UZ-QR": "Qoraqalpog'iston",
};

// Pul miqdorini o'qib bo'lish formatga o'gir: 1230000000 → "1.23 mlrd so'm"
export function formatUZS(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1e12) return `${(value / 1e12).toFixed(2)} trln so'm`;
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)} mlrd so'm`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)} mln so'm`;
  return `${Math.round(value).toLocaleString("uz-UZ")} so'm`;
}

// Risk darajasi → Tailwind bg klassi (badge fon rangi)
export function riskColor(level: string): string {
  if (level === "high") return "bg-red-600";
  if (level === "medium") return "bg-amber-500";
  return "bg-emerald-500";
}

// Risk darajasi → Tailwind text klassi
export function riskTextColor(level: string): string {
  if (level === "high") return "text-red-500";
  if (level === "medium") return "text-amber-400";
  return "text-emerald-400";
}
