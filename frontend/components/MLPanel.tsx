import type { Lot } from "@/lib/api";

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

function divergenceText(rule: number, ml: number): string | null {
  // ml is 0..1, rule is 0..100
  const ruleNorm = rule / 100;
  const diff = Math.abs(ruleNorm - ml);
  if (diff < 0.3) return null;
  if (ruleNorm > ml) {
    return (
      "Rule engine xalqaro standart asosida ko'p signal topdi. " +
      "ML model trening data'sida bu pattern keng tarqalganligi sabab past baholaydi."
    );
  }
  return (
    "ML model rule'lar qoplay olmaydigan murakkab pattern (masalan bankruptcy + no-discount) topdi. " +
    "Bu signal'lar OECD ramkasida yo'q — ML statistik tahlildan kelgan."
  );
}

export function MLPanel({ lot }: { lot: Lot }) {
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
              <div className="mono text-[10px] text-[var(--fg-dim)]">
                shubhali ehtimol
              </div>
            </div>
          )}
          {lot.ml_iso_score !== null && lot.ml_iso_score !== undefined && (
            <div>
              <div className="kicker text-[10px]">IsolationForest</div>
              <div className="mono tabnum text-lg font-semibold text-[var(--fg)] mt-0.5">
                {lot.ml_iso_score.toFixed(3)}
              </div>
              <div className="mono text-[10px] text-[var(--fg-dim)]">
                anomaly score
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
