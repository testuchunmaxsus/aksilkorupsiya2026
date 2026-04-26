"use client";
// Birinchi tashriffda ko'rinadigan "Bu nima?" banner.
// Keyin localStorage'da saqlanadi, lekin har vaqt qayta ochish mumkin:
//   - URL'da ?welcome=1 bo'lsa
//   - Boshqa joydan window.dispatchEvent(new Event("aw:show-onboarding")) chaqirilsa
import { useEffect, useState } from "react";

const STORAGE_KEY = "aw_onboarded";
const SHOW_EVENT = "aw:show-onboarding";

// Tashqi joylardan chaqirish uchun helper (NavBar tugmasi ishlatadi)
export function openOnboarding() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(SHOW_EVENT));
  }
}

export function Onboarding() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // 1) Birinchi tashriff bo'lsa avtomatik ko'rsatish
    try {
      const url = new URL(window.location.href);
      const force = url.searchParams.get("welcome") === "1";
      if (force || !localStorage.getItem(STORAGE_KEY)) {
        setShow(true);
      }
    } catch {
      /* private mode */
    }

    // 2) Boshqa joydan event keladi — ochamiz
    const handler = () => setShow(true);
    window.addEventListener(SHOW_EVENT, handler);
    return () => window.removeEventListener(SHOW_EVENT, handler);
  }, []);

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {}
    setShow(false);
    // URL'dan ?welcome=1 ni olib tashlash (toza tarix uchun)
    try {
      const url = new URL(window.location.href);
      if (url.searchParams.has("welcome")) {
        url.searchParams.delete("welcome");
        window.history.replaceState({}, "", url.toString());
      }
    } catch {}
  };

  if (!show) return null;

  return (
    <div className="mx-auto max-w-7xl px-6 mt-4">
      <div
        className="rounded-2xl border-2 border-[var(--primary)] p-5 md:p-6 relative overflow-hidden"
        style={{
          background:
            "linear-gradient(135deg, var(--primary-soft) 0%, #ffffff 100%)",
        }}
      >
        <button
          onClick={dismiss}
          aria-label="Yopish"
          className="absolute top-3 right-3 h-7 w-7 rounded-full bg-white/80 hover:bg-white text-[var(--fg-mute)] hover:text-[var(--fg)] flex items-center justify-center text-lg leading-none"
          type="button"
        >
          ×
        </button>

        <div className="flex items-start gap-4">
          <span className="text-4xl select-none">👋</span>
          <div className="flex-1 min-w-0">
            <div className="font-bold text-xl text-[var(--fg)] leading-tight">
              AuksionWatch nima?
            </div>
            <p className="mt-2 text-sm md:text-base text-[var(--fg-mute)] leading-relaxed">
              Davlat mol-mulki auksionlarida shubhali sxemalarni AI yordamida
              topadigan mustaqil monitoring tizimi. 11,000+ lot bizda tahlilda.
            </p>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
              <Step
                num={1}
                title="Lotni qidiring"
                desc="Raqam, manzil yoki sotuvchi nomi bo'yicha"
              />
              <Step
                num={2}
                title="Risk darajasini ko'ring"
                desc="🚩 shubhali, ⚠️ diqqatli, ✓ normal"
              />
              <Step
                num={3}
                title="Harakat qiling"
                desc="Ulashing, signal yuboring, sud tekshiring"
              />
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <button
                onClick={dismiss}
                className="btn btn-primary"
                type="button"
              >
                Boshlash
              </button>
              <button
                onClick={async () => {
                  // Eng yuqori risk score'li lotni dinamik topib o'sha sahifaga o'tamiz.
                  // Hardcoded lot id ishonchsiz — DB o'zgarib turadi.
                  try {
                    const apiBase =
                      process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
                    const r = await fetch(
                      `${apiBase}/api/lots?risk_level=high&limit=1`,
                      { cache: "no-store" }
                    );
                    const d = await r.json();
                    const id = d?.items?.[0]?.id;
                    dismiss();
                    if (id) window.location.href = `/lot/${id}`;
                    else window.location.href = "/lots?risk_level=high";
                  } catch {
                    dismiss();
                    window.location.href = "/lots?risk_level=high";
                  }
                }}
                className="btn btn-outline"
                type="button"
              >
                Demo lot ko&apos;rsatish
              </button>
              <a
                href="/methodology"
                className="text-sm text-[var(--primary)] hover:underline ml-1"
              >
                Metodologiya haqida →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Step({ num, title, desc }: { num: number; title: string; desc: string }) {
  return (
    <div className="flex gap-3 items-start">
      <span className="flex-shrink-0 inline-flex h-7 w-7 rounded-full bg-[var(--primary)] text-white items-center justify-center font-bold text-sm">
        {num}
      </span>
      <div className="min-w-0">
        <div className="font-semibold text-[var(--fg)] text-sm">{title}</div>
        <div className="text-xs text-[var(--fg-mute)] mt-0.5">{desc}</div>
      </div>
    </div>
  );
}
