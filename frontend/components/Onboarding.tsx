"use client";
// Birinchi tashriffda chiqadigan "Bu nima?" banner.
// localStorage'da `aw_onboarded=1` saqlangach qayta ko'rinmaydi.
import { useEffect, useState } from "react";

const STORAGE_KEY = "aw_onboarded";

export function Onboarding() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) {
        setShow(true);
      }
    } catch {
      /* private mode — banner ko'rinmaydi */
    }
  }, []);

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {}
    setShow(false);
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
              <a
                href="/lot/23439577"
                onClick={dismiss}
                className="btn btn-outline"
              >
                Demo lot ko'rsatish
              </a>
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
