"use client";

import { useEffect, useRef, useState } from "react";
import type { MapMarker } from "@/lib/api";
import Link from "next/link";

export function LotMap({ markers }: { markers: MapMarker[] }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!mapRef.current) return;

    let map: any;
    (async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet/dist/leaflet.css");

      map = L.map(mapRef.current!, { zoomControl: true }).setView(
        [41.5, 64.5],
        6
      );
      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution: "© OpenStreetMap",
          maxZoom: 18,
        }
      ).addTo(map);

      const colorFor = (level: string) =>
        level === "high"
          ? "#dc2626"
          : level === "medium"
          ? "#f59e0b"
          : "#10b981";

      markers.forEach((m) => {
        const radius = m.level === "high" ? 12 : m.level === "medium" ? 8 : 5;
        const circle = L.circleMarker([m.lat, m.lon], {
          radius,
          fillColor: colorFor(m.level),
          color: "#000",
          weight: 1,
          opacity: 0.9,
          fillOpacity: 0.85,
        }).addTo(map);
        circle.bindPopup(
          `<div style="font-family:sans-serif;min-width:200px">
            <div style="font-weight:600;color:${colorFor(m.level)};margin-bottom:4px">
              ${m.level === "high" ? "🚩 YUQORI XAVF" : m.level === "medium" ? "⚠️ O'RTA XAVF" : "✓ Oz xavf"} · ${Math.round(m.risk)}
            </div>
            <div style="margin-bottom:6px">${m.title}</div>
            <a href="/lot/${m.id}" style="color:#dc2626;font-weight:600;text-decoration:underline">Batafsil →</a>
          </div>`
        );
      });
      setReady(true);
    })();

    return () => {
      map?.remove();
    };
  }, [markers]);

  return (
    <div className="relative">
      <div
        ref={mapRef}
        className="h-[600px] w-full rounded-xl overflow-hidden border border-zinc-800"
      />
      {!ready && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/60 text-zinc-400 rounded-xl">
          Xarita yuklanmoqda...
        </div>
      )}
      <Legend />
    </div>
  );
}

function Legend() {
  return (
    <div className="absolute bottom-4 right-4 z-[1000] rounded-lg border border-zinc-700 bg-zinc-900/95 p-3 text-xs text-zinc-300 shadow-lg">
      <div className="font-semibold mb-2 text-white">Xavf darajasi</div>
      {[
        { label: "Yuqori (70+)", c: "#dc2626" },
        { label: "O'rta (40-69)", c: "#f59e0b" },
        { label: "Oz (<40)", c: "#10b981" },
      ].map((row) => (
        <div key={row.label} className="flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 rounded-full"
            style={{ background: row.c }}
          />
          {row.label}
        </div>
      ))}
    </div>
  );
}
