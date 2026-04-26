"use client";
// "?" tugmasi — istalgan vaqtda Onboarding banner'ni qayta ochadi.
// NavBar yuqori strip'iga joylashtirilgan.
import { openOnboarding } from "./Onboarding";

export function HelpButton() {
  return (
    <button
      onClick={openOnboarding}
      title="Bu sayt haqida"
      aria-label="Yordam"
      type="button"
      className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-white/15 hover:bg-white/25 text-white text-[11px] font-bold transition-colors"
    >
      ?
    </button>
  );
}
