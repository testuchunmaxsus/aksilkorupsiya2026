"use client";

import dynamic from "next/dynamic";
import { useMemo, useRef, useEffect } from "react";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

type GraphData = {
  nodes: { id: string; type: string; label: string; value: number; risk?: number }[];
  edges: { source: string; target: string; value: number }[];
};

export function NetworkGraph({ data }: { data: GraphData }) {
  const fgRef = useRef<any>(null);

  const graphData = useMemo(
    () => ({
      nodes: data.nodes.map((n) => ({
        ...n,
        val: n.type === "seller" ? Math.max(4, Math.log2(n.value + 1) * 3) : 12,
      })),
      links: data.edges.map((e) => ({
        source: e.source,
        target: e.target,
        value: e.value,
      })),
    }),
    [data]
  );

  useEffect(() => {
    if (fgRef.current) {
      // Slow gentle zoom-out so user sees full graph
      fgRef.current.zoomToFit(400, 60);
    }
  }, [graphData]);

  return (
    <div className="relative h-[640px] w-full bg-[var(--bg-elev)] border border-[var(--line)] overflow-hidden">
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={(node: any) =>
          node.type === "seller"
            ? `${node.label}\n${node.value} lot · risk ${node.risk ?? "?"}`
            : `Hudud: ${node.label}`
        }
        nodeColor={(node: any) => {
          if (node.type === "region") return "#52525b";
          const risk = node.risk || 0;
          if (risk >= 70) return "#ef4444";
          if (risk >= 40) return "#f59e0b";
          return "#10b981";
        }}
        nodeRelSize={6}
        linkColor={() => "rgba(255,255,255,0.15)"}
        linkWidth={(l: any) => Math.max(0.5, Math.log2(l.value + 1) * 0.5)}
        backgroundColor="transparent"
        cooldownTicks={150}
        nodeCanvasObjectMode={() => "after"}
        nodeCanvasObject={(node: any, ctx: any, scale: number) => {
          if (node.type === "region" || node.value > 200) {
            const fontSize = 11 / scale;
            ctx.font = `${fontSize}px Inter, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle =
              node.type === "region" ? "#a1a1aa" : "#fafafa";
            ctx.fillText(
              node.label.slice(0, 28),
              node.x,
              node.y + (node.val + 4) / scale
            );
          }
        }}
      />
      <div className="absolute bottom-3 right-3 z-10 rounded border border-[var(--line)] bg-[var(--bg)] p-3 text-xs space-y-1.5">
        <div className="kicker">LEGEND</div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#ef4444" }} />
          <span className="text-zinc-300">Yuqori xavf (risk ≥ 70)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#f59e0b" }} />
          <span className="text-zinc-300">O&apos;rta (40-69)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#10b981" }} />
          <span className="text-zinc-300">Past (&lt;40)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#52525b" }} />
          <span className="text-zinc-300">Hudud</span>
        </div>
      </div>
    </div>
  );
}
