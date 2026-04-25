"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

type Point = {
  month: string;
  total: number;
  high: number;
  medium: number;
  closed: number;
  value: number;
};

export function TrendChart({ data }: { data: Point[] }) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-500 text-sm">
        Vaqt ma&apos;lumotlari yetarli emas
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 12, right: 12, bottom: 8, left: 0 }}>
        <defs>
          <linearGradient id="totalG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#a1a1aa" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#a1a1aa" stopOpacity={0.05} />
          </linearGradient>
          <linearGradient id="highG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.7} />
            <stop offset="100%" stopColor="#ef4444" stopOpacity={0.05} />
          </linearGradient>
          <linearGradient id="closedG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.6} />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#27272d" strokeDasharray="2 4" vertical={false} />
        <XAxis
          dataKey="month"
          stroke="#71717a"
          fontSize={11}
          tickMargin={8}
        />
        <YAxis
          stroke="#71717a"
          fontSize={11}
          tickMargin={4}
        />
        <Tooltip
          contentStyle={{
            background: "#0b0b0d",
            border: "1px solid #27272d",
            borderRadius: 0,
            fontSize: 12,
          }}
          labelStyle={{ color: "#fafafa", fontWeight: 600 }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: "#a1a1aa" }}
          iconType="square"
        />
        <Area
          type="monotone"
          dataKey="total"
          stroke="#a1a1aa"
          strokeWidth={1}
          fill="url(#totalG)"
          name="Jami lotlar"
        />
        <Area
          type="monotone"
          dataKey="high"
          stroke="#ef4444"
          strokeWidth={2}
          fill="url(#highG)"
          name="Yuqori xavfli"
        />
        <Area
          type="monotone"
          dataKey="closed"
          stroke="#f59e0b"
          strokeWidth={1.5}
          fill="url(#closedG)"
          name="Yopiq auksion"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
