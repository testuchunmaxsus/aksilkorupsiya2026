// Sodda til VERDICT — texnik raqamlarsiz, har kim tushunadi.
// Lot detail sahifasi tepasida ko'rinadi, gauge'lardan oldin.
import type { Lot } from "@/lib/api";

type Tone = "alarm" | "warn" | "ok";

type Verdict = {
  tone: Tone;
  emoji: string;
  headline: string;
  reasons: string[];
};

// Risk + ML score'larni birlashtirib, eng yuqori darajani oladi
function combinedTone(lot: Lot): Tone {
  const ruleHigh = lot.risk_score >= 70 || lot.risk_level === "high";
  const mlHigh = lot.ml_level === "KRITIK" || lot.ml_level === "YUQORI";
  const ruleMid = lot.risk_score >= 40;
  const mlMid = lot.ml_level === "O'RTA";
  if (ruleHigh || mlHigh) return "alarm";
  if (ruleMid || mlMid) return "warn";
  return "ok";
}

// Top 3 flag'ni sodda til jumlasiga aylantirish
function plainReasons(lot: Lot): string[] {
  const flags = (lot.flags || []).slice().sort((a, b) => b.score - a.score);
  const seen = new Set<string>();
  const out: string[] = [];

  for (const f of flags) {
    // Bir necha o'xshash flag'larni filtrlash (misol: 3 ta below_appraisal)
    const key = f.type.replace(/_severe|_strong|_mild/g, "");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(f.title);
    if (out.length >= 3) break;
  }

  // ML reason ham qo'shamiz, agar ham mavjud bo'lsa
  if (lot.ml_reason && out.length < 3) {
    out.push(`AI tahlil: ${lot.ml_reason}`);
  }
  return out;
}

function buildVerdict(lot: Lot): Verdict {
  const tone = combinedTone(lot);
  const reasons = plainReasons(lot);

  if (tone === "alarm") {
    return {
      tone,
      emoji: "🚩",
      headline: "Bu lot jiddiy tekshirilishi kerak",
      reasons,
    };
  }
  if (tone === "warn") {
    return {
      tone,
      emoji: "⚠️",
      headline: "Bu lotda diqqatli bo'ling",
      reasons,
    };
  }
  return {
    tone,
    emoji: "✓",
    headline: "Bu lotda alohida shubhali belgi topilmadi",
    reasons,
  };
}

export function VerdictHeader({ lot }: { lot: Lot }) {
  const v = buildVerdict(lot);

  // Rang sxemasi har holat uchun
  const palette = {
    alarm: {
      bg: "linear-gradient(135deg, var(--red-soft) 0%, #fff 100%)",
      border: "var(--red)",
      titleColor: "var(--red)",
    },
    warn: {
      bg: "linear-gradient(135deg, var(--amber-soft) 0%, #fff 100%)",
      border: "var(--amber)",
      titleColor: "var(--amber)",
    },
    ok: {
      bg: "linear-gradient(135deg, var(--emerald-soft) 0%, #fff 100%)",
      border: "var(--emerald)",
      titleColor: "var(--emerald)",
    },
  }[v.tone];

  return (
    <section
      className="rounded-2xl border-2 p-6 md:p-8"
      style={{
        background: palette.bg,
        borderColor: palette.border,
      }}
    >
      <div className="flex items-start gap-4">
        <span className="text-5xl md:text-6xl select-none">{v.emoji}</span>
        <div className="flex-1 min-w-0">
          <h2
            className="text-2xl md:text-3xl font-bold leading-tight"
            style={{ color: palette.titleColor }}
          >
            {v.headline}
          </h2>
          {v.reasons.length > 0 && (
            <ul className="mt-3 space-y-1.5 text-[var(--fg)] text-base">
              {v.reasons.map((r, i) => (
                <li key={i} className="flex gap-2">
                  <span className="opacity-50">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
