"use client";

export function PrintButton() {
  return (
    <button
      onClick={() => window.print()}
      className="inline-flex items-center gap-1.5 border border-[var(--line)] px-3 py-1.5 mono text-[10px] tracking-widest text-zinc-300 hover:border-zinc-400 hover:text-white transition-colors"
    >
      <span>📄</span>
      HISOBOT (PDF)
    </button>
  );
}
