import { api } from "@/lib/api";
import { NetworkGraph } from "@/components/NetworkGraph";

export const dynamic = "force-dynamic";

export default async function NetworkPage() {
  const data = await api.network(80).catch(() => ({ nodes: [], edges: [] }));
  const sellerNodes = data.nodes.filter((n) => n.type === "seller").length;
  const regionNodes = data.nodes.filter((n) => n.type === "region").length;

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="border-b border-[var(--line)] pb-6">
        <div className="kicker">SOTUVCHI-HUDUD GRAPH · NETWORKX</div>
        <h1 className="headline mt-2 text-4xl text-white">
          Sotuvchilar tarmog&apos;i
        </h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          TOP {sellerNodes} sotuvchi ({regionNodes} hudud bo&apos;yicha) interaktiv tarmoq
          xaritasi. Markaz tomonidagi yirik qizil tugunlar — eng xavfli sotuvchilar.
          Tugun ustiga olib boring — ma&apos;lumot ko&apos;rinadi. Bu metodologiya{" "}
          <em className="text-zinc-200 not-italic">Mihály Fazekas state capture</em>{" "}
          tahlilidan ilhomlantirilgan.
        </p>
      </header>

      <section className="mt-6 grid grid-cols-3 md:grid-cols-5 gap-3">
        <Stat label="Sotuvchilar" value={sellerNodes} />
        <Stat label="Hududlar" value={regionNodes} />
        <Stat label="Bog&apos;lanishlar" value={data.edges.length} />
        <Stat
          label="Yuqori xavfli"
          value={data.nodes.filter((n) => (n.risk || 0) >= 70).length}
          color="var(--red)"
        />
        <Stat
          label="O'rta xavf"
          value={data.nodes.filter((n) => (n.risk || 0) >= 40 && (n.risk || 0) < 70).length}
          color="var(--amber)"
        />
      </section>

      <section className="mt-6">
        <NetworkGraph data={data} />
      </section>

      <section className="mt-8 grid md:grid-cols-2 gap-6">
        <div className="card p-5">
          <div className="kicker mb-2">QANDAY O&apos;QILADI</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            <li>
              <span className="text-[var(--red)] mono">●</span>{" "}
              <strong>Tugun (node)</strong> = sotuvchi yoki hudud
            </li>
            <li>
              <span className="text-[var(--red)] mono">●</span>{" "}
              <strong>Hajmi</strong> — sotuvchining lotlari soni (logaritmik)
            </li>
            <li>
              <span className="text-[var(--red)] mono">●</span>{" "}
              <strong>Rangi</strong> — o&apos;rtacha risk darajasi
            </li>
            <li>
              <span className="text-[var(--red)] mono">●</span>{" "}
              <strong>Chiziq (edge)</strong> = sotuvchi va hudud bog&apos;lanishi (lot soni)
            </li>
          </ul>
        </div>
        <div className="card p-5">
          <div className="kicker mb-2">METODOLOGIYA</div>
          <p className="text-sm text-zinc-300">
            Bu graf — bo&apos;lajak versiyada{" "}
            <strong>NetworkX Louvain community detection</strong> bilan
            kengaytiriladi. Hozirgi vizualizatsiya — Force-directed layout
            (D3.js asosida).
            <br />
            <br />
            Bo&apos;lajak qadamlar:
            <br />· Sotuvchi-g&apos;olib edge (kim sotgan, kim olgan)
            <br />· Affilirlangan firmalar klasteri (community)
            <br />· Vaqt o&apos;tishi bilan tarmoq dinamikasi
          </p>
        </div>
      </section>
    </main>
  );
}

function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="card px-4 py-3">
      <div className="kicker text-[10px]">{label}</div>
      <div
        className="headline mt-1 text-2xl tabnum"
        style={{ color: color || "white" }}
      >
        {value}
      </div>
    </div>
  );
}
