// Asosiy sayt navigatsiya paneli — har sahifada ko'rinadi (layout.tsx orqali).
// my.gov.uz ga o'xshatib 2 ta strip: yuqori (mini-bar) + asosiy (logo + menu).
import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";
import { HelpButton } from "./HelpButton";

export function NavBar() {
  return (
    <header className="bg-[var(--bg-elev)] border-b border-[var(--line)] sticky top-0 z-50">
      {/* Yuqori strip — gov portal stili: status, til, API, tema */}
      <div className="bg-[var(--primary-deep)] text-white">
        <div className="mx-auto max-w-7xl px-6 py-1.5 flex items-center justify-between text-[11px]">
          {/* Chap tomon — live status indikatori */}
          <div className="flex items-center gap-2 mono tracking-wider">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 live-dot" />
            <span>OCHIQ NAZORAT TIZIMI · MUSTAQIL</span>
          </div>
          {/* O'ng tomon — quick links + help + theme */}
          <div className="flex items-center gap-3 text-white/70 mono">
            {/* "?" — Onboarding banner'ni istalgan vaqtda qayta ochish */}
            <HelpButton />
            <span className="opacity-40">|</span>
            <span>UZ</span>
            <span className="opacity-40">|</span>
            <a className="hover:text-white" href={`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/docs`} target="_blank" rel="noreferrer">
              API
            </a>
            <span className="opacity-40">|</span>
            <Link className="hover:text-white" href="/methodology">
              Metodologiya
            </Link>
            <span className="opacity-40">|</span>
            <ThemeToggle />
          </div>
        </div>
      </div>

      {/* Asosiy bar — logo + menyu + CTA */}
      <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between gap-6 bg-[var(--bg-elev)]">
        {/* Logo (bosh sahifaga link) */}
        <Link href="/" className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.png"
            alt="AuksionWatch"
            className="h-11 md:h-12 w-auto"
            draggable={false}
          />
          {/* Mobile'da yashirilgan — faqat sm+ ekran */}
          <span className="hidden sm:inline-block text-[11px] text-[var(--fg-dim)] border-l border-[var(--line)] pl-3">
            Ochiq nazorat<br />tizimi
          </span>
        </Link>

        {/* Asosiy menyu — lg+ ekran */}
        <nav className="hidden lg:flex items-center gap-1 text-sm font-medium">
          {[
            ["/", "Bosh"],
            ["/lots", "Lotlar"],
            ["/map", "Xarita"],
            ["/sellers", "Sotuvchilar"],
            ["/network", "Tarmoq"],
            ["/pep", "PEP"],
          ].map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className="px-3 py-2 text-[var(--fg-mute)] hover:text-[var(--primary)] hover:bg-[var(--primary-soft)] rounded-md transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* O'ng tarafdagi CTA — eng xavfli lotlarga tezkor o'tish */}
        <div className="flex items-center gap-2">
          <Link
            href="/lots?risk_level=high"
            className="btn btn-danger hidden md:inline-flex"
          >
            <span className="inline-block h-2 w-2 rounded-full bg-white live-dot" />
            Qizil bayroqlar
          </Link>
        </div>
      </div>
    </header>
  );
}
