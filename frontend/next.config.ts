import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: undefined,
  experimental: {
    optimizePackageImports: ["recharts", "leaflet", "react-leaflet"],
  },
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
