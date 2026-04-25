import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { NavBar } from "@/components/NavBar";
import Link from "next/link";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono-loaded",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AuksionWatch — E-AUKSION ochiq nazorat tizimi",
  description:
    "Davlat mol-mulki auksionlaridagi shubhali sxemalarni xalqaro standartlar (OECD, UNCAC, OCDS) asosida AI yordamida aniqlovchi mustaqil monitoring tizimi.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="uz"
      className={`${inter.variable} ${mono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');if(!t){t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`,
          }}
        />
      </head>
      <body
        className="min-h-full flex flex-col bg-[var(--bg)] text-[var(--fg)]"
        style={{
          fontFamily:
            "var(--font-inter), Inter, ui-sans-serif, system-ui, sans-serif",
        }}
      >
        <NavBar />
        <div className="flex-1">{children}</div>

        <footer className="mt-20 bg-[var(--bg-elev)] border-t border-[var(--line)]">
          <div className="mx-auto max-w-7xl px-6 py-10 grid md:grid-cols-4 gap-8">
            <div className="md:col-span-1">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/logo.png"
                alt="AuksionWatch"
                className="h-12 w-auto mb-4"
                draggable={false}
              />
              <p className="text-sm text-[var(--fg-mute)] leading-relaxed">
                E-AUKSION ochiq nazorat tizimi. Davlat mol-mulki auksionlarini
                xalqaro standartlar asosida tahlil qiluvchi mustaqil monitoring tizim.
              </p>
            </div>

            <div>
              <div className="kicker mb-3">PLATFORMA</div>
              <ul className="space-y-2 text-sm">
                <li><Link className="text-[var(--fg-mute)] hover:text-[var(--primary)]" href="/lots">Lotlar reestri</Link></li>
                <li><Link className="text-[var(--fg-mute)] hover:text-[var(--primary)]" href="/map">Xarita</Link></li>
                <li><Link className="text-[var(--fg-mute)] hover:text-[var(--primary)]" href="/sellers">Sotuvchilar reytingi</Link></li>
                <li><Link className="text-[var(--fg-mute)] hover:text-[var(--primary)]" href="/network">Sotuvchilar tarmog&apos;i</Link></li>
                <li><Link className="text-[var(--fg-mute)] hover:text-[var(--primary)]" href="/pep">PEP signal&apos;lari</Link></li>
              </ul>
            </div>

            <div>
              <div className="kicker mb-3">RESURSLAR</div>
              <ul className="space-y-2 text-sm">
                <li><Link className="text-[var(--fg-mute)] hover:text-[var(--primary)]" href="/methodology">Metodologiya</Link></li>
                <li><a className="text-[var(--fg-mute)] hover:text-[var(--primary)]" target="_blank" rel="noreferrer" href="http://127.0.0.1:8000/docs">REST API hujjati</a></li>
                <li><a className="text-[var(--fg-mute)] hover:text-[var(--primary)]" target="_blank" rel="noreferrer" href="http://127.0.0.1:8000/api/export.csv">CSV eksport</a></li>
                <li><a className="text-[var(--fg-mute)] hover:text-[var(--primary)]" target="_blank" rel="noreferrer" href="http://127.0.0.1:8000/api/export.json">JSON eksport</a></li>
              </ul>
            </div>

            <div>
              <div className="kicker mb-3">MA&apos;LUMOT MANBASI</div>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    className="link-u"
                    target="_blank"
                    rel="noreferrer"
                    href="https://e-auksion.uz"
                  >
                    e-auksion.uz
                  </a>
                </li>
                <li className="text-[var(--fg-mute)] text-xs">Public sitemap + rasmiy Excel hisobotlari</li>
                <li className="mt-3">
                  <span className="pill primary">CC BY-SA 4.0</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-[var(--line)] py-4">
            <div className="mx-auto max-w-7xl px-6 flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--fg-dim)]">
              <div>
                AuksionWatch v1.2 · Aksilkorrupsiya hackathon 2026
              </div>
              <div className="flex items-center gap-3">
                <span>OECD</span>
                <span>·</span>
                <span>UNCAC Art.9</span>
                <span>·</span>
                <span>OCDS</span>
                <span>·</span>
                <span>FATF R12</span>
              </div>
            </div>
            <div className="mx-auto max-w-7xl px-6 mt-2 text-[11px] text-[var(--fg-dim)]">
              Loyiha rasmiy davlat organlari bilan bog&apos;liq emas. Xalqaro
              standartlar (OECD, World Bank, UNCAC, OCDS) asosida ochiq
              ma&apos;lumotlardan foydalangan holda yaratilgan. Aniqlangan
              signal&apos;lar qonuniy aybdorlik degani emas — tekshirish uchun
              ko&apos;rsatma.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
