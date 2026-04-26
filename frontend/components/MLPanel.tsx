// ML Ensemble paneli — lot detail sahifasida CategoryBars ostida ko'rinadi.
// XGBoost + IsolationForest natijalarini ko'rsatadi va rule engine bilan
// side-by-side taqqoslaydi. Agar score'lar bir-biridan jiddiy farq qilsa
// (>30 punkt) avtomatik tushuntirish chiqaradi.
import type { Lot } from "@/lib/api";

// ML level → rang (KRITIK=qizil, YUQORI=amber, O'RTA=ko'k, PAST=yashil)
const LEVEL_COLOR: Record<string, string> = {
  KRITIK: "var(--red)",
  YUQORI: "#f59e0b",
  "O'RTA": "#0080d6",
  PAST: "var(--emerald)",
};

const LEVEL_BG: Record<string, string> = {
  KRITIK: "var(--red-soft)",
  YUQORI: "#fff7ed",
  "O'RTA": "var(--primary-soft)",
  PAST: "var(--emerald-soft)",
};

// Agar rule va ML score'lari sezilarli farq qilsa — sababini tushuntirish.
// Misol: rule=100 + ml=20 → rule "ko'p signal", ml "training pattern keng tarqalgan"
// Misol: rule=35 + ml=92 → ml "murakkab pattern, OECD ramkasidan tashqari"
function divergenceText(rule: number, ml: number): string | null {
  // ml 0..1, rule 0..100 — bir o'lchovga keltirish
  const ruleNorm = rule / 100;
  const diff = Math.abs(ruleNorm - ml);
  if (diff < 0.3) return null;  // farq kichik — tushuntirish kerakmas
  if (ruleNorm > ml) {
    // Rule yuqori, ML past
    return (
      "Rule engine xalqaro standart asosida ko'p signal topdi. " +
      "ML model trening data'sida bu pattern keng tarqalganligi sabab past baholaydi."
    );
  }
  // ML yuqori, rule past
  return (
    "ML model rule'lar qoplay olmaydigan murakkab pattern (masalan bankruptcy + no-discount) topdi. " +
    "Bu signal'lar OECD ramkasida yo'q — ML statistik tahlildan kelgan."
  );
}

// AI ishonch darajasini sodda tilga aylantirish (XGBoost ehtimoli 0..1)
function confidenceLabel(prob: number): string {
  if (prob >= 0.85) return "Juda yuqori (85%+)";
  if (prob >= 0.65) return "Yuqori (65–85%)";
  if (prob >= 0.40) return "O'rtacha (40–65%)";
  return "Past (40% dan kam)";
}

// IsoForest anomaly score interpretatsiyasi (-0.5..0.5 oraliqda, manfiy = anomaliya)
function anomalyLabel(score: number): string {
  if (score < -0.15) return "Kuchli anomaliya — boshqa lotlardan keskin farq";
  if (score < 0) return "Yengil anomaliya — biroz noaniq pattern";
  return "Normal — boshqa lotlarga o'xshash";
}

export function MLPanel({ lot }: { lot: Lot }) {
  // ML score yo'q bo'lsa panel'ni umuman ko'rsatmaymiz
  if (lot.ml_score === null || lot.ml_score === undefined) return null;
  const level = lot.ml_level || "PAST";
  const color = LEVEL_COLOR[level] || "var(--fg-mute)";
  const bg = LEVEL_BG[level] || "var(--bg-soft)";
  const score = (lot.ml_score * 100).toFixed(0);
  const ruleScore = lot.risk_score;
  const divergence = divergenceText(ruleScore, lot.ml_score);

  return (
    <div className="card overflow-hidden">
      <div
        className="border-b border-[var(--line)] px-5 py-3"
        style={{ background: bg }}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="kicker">ML ENSEMBLE · XGBoost + IsolationForest</div>
            <div className="font-bold text-[var(--fg)]">
              ML xulosa: <span style={{ color }}>{level}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold tabnum" style={{ color }}>
              {score}
              <span className="text-sm font-medium opacity-60">/100</span>
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 py-4 space-y-3">
        {/* Sodda tildagi AI xulosa — "bu nima degani" */}
        <div className="rounded-lg bg-[var(--bg-soft)] border border-[var(--line)] px-3 py-2.5">
          <div className="flex items-start gap-2">
            <span className="text-base flex-shrink-0">🤖</span>
            <div className="text-sm text-[var(--fg)] leading-relaxed">
              <strong>AI xulosasi:</strong>{" "}
              {level === "KRITIK"
                ? "model bu lotni juda shubhali deb baholadi — yetuk korrupsiya signallari bor."
                : level === "YUQORI"
                ? "model lotda jiddiy xavf belgilarini topdi — tekshirish tavsiya etiladi."
                : level === "O'RTA"
                ? "ba'zi anomaliyalar bor, lekin keskin signal yo'q — kuzatuvga olish ma'qul."
                : "model bu lotni normal deb baholadi — boshqa lotlardan farq qilmaydi."}
              <details className="mt-1.5 cursor-pointer">
                <summary className="text-xs text-[var(--primary)] hover:underline list-none">
                  Bu raqamlar nima degani? ▾
                </summary>
                <div className="mt-2 text-xs text-[var(--fg-mute)] leading-relaxed">
                  ML modelimiz har lotni 33 ta xususiyat (narx, takror, sotuvchi
                  tarixi, va h.k.) bo&apos;yicha taqqoslaydi va ikkita algoritm
                  yordamida ball beradi:
                  <ul className="mt-1 ml-4 list-disc space-y-0.5">
                    <li><strong>XGBoost</strong> — &quot;bu lotning shubhali bo&apos;lish ehtimoli necha foiz?&quot;</li>
                    <li><strong>IsolationForest</strong> — &quot;bu lot boshqalardan qanchalik farq qiladi?&quot;</li>
                  </ul>
                  Ikkalasi birga &quot;ensemble&quot; ball beradi (0–100). 70+ ball
                  &quot;KRITIK&quot;, 40–70 &quot;YUQORI&quot; va h.k.
                </div>
              </details>
            </div>
          </div>
        </div>

        {/* Side-by-side comparison with rule engine */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="rounded-lg border border-[var(--line)] p-3">
            <div className="kicker text-[10px]">RULE ENGINE</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span
                className="text-2xl font-bold tabnum"
                style={{
                  color:
                    ruleScore >= 70
                      ? "var(--red)"
                      : ruleScore >= 40
                      ? "var(--amber)"
                      : "var(--emerald)",
                }}
              >
                {Math.round(ruleScore)}
              </span>
              <span className="text-xs text-[var(--fg-dim)]">/100</span>
            </div>
            <div className="text-[10px] text-[var(--fg-mute)] mt-1">
              OECD · Fazekas · 18+ rule
            </div>
          </div>
          <div
            className="rounded-lg border p-3"
            style={{ borderColor: color, background: bg }}
          >
            <div className="kicker text-[10px]">ML ENSEMBLE</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold tabnum" style={{ color }}>
                {score}
              </span>
              <span className="text-xs text-[var(--fg-dim)]">/100</span>
            </div>
            <div className="text-[10px] text-[var(--fg-mute)] mt-1">
              33 feature · CV AUC 0.98
            </div>
          </div>
        </div>

        {divergence && (
          <div className="rounded-lg bg-[var(--bg-soft)] border border-[var(--line)] px-3 py-2 text-xs leading-relaxed text-[var(--fg-mute)]">
            <span className="font-semibold text-[var(--fg)]">Nima uchun farq?</span>{" "}
            {divergence}
          </div>
        )}

        {lot.ml_reason && (
          <div>
            <div className="kicker mb-1">ML sababi</div>
            <p className="text-sm text-[var(--fg)] leading-relaxed">
              {lot.ml_reason}
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[var(--line-soft)]">
          {lot.ml_xgb_prob !== null && lot.ml_xgb_prob !== undefined && (
            <div>
              <div className="kicker text-[10px]">XGBoost (CV AUC 0.98)</div>
              <div className="mono tabnum text-lg font-semibold text-[var(--fg)] mt-0.5">
                {(lot.ml_xgb_prob * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-[var(--fg-mute)] mt-0.5">
                Ishonch: <strong>{confidenceLabel(lot.ml_xgb_prob)}</strong>
              </div>
            </div>
          )}
          {lot.ml_iso_score !== null && lot.ml_iso_score !== undefined && (
            <div>
              <div className="kicker text-[10px]">IsolationForest</div>
              <div className="mono tabnum text-lg font-semibold text-[var(--fg)] mt-0.5">
                {lot.ml_iso_score.toFixed(3)}
              </div>
              <div className="text-[11px] text-[var(--fg-mute)] mt-0.5">
                {anomalyLabel(lot.ml_iso_score)}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-[var(--line)] px-5 py-2.5 text-[10px] mono text-[var(--fg-dim)] uppercase tracking-wider leading-relaxed bg-[var(--bg-soft)]">
        Ensemble: rules×0.40 + XGBoost×0.35 + IsoForest×0.25 · Rule engine va ML
        bir-birini to&apos;ldiradi
      </div>
    </div>
  );
}
