import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    if (process.env.NODE_ENV !== "development" || !process.env.FASTAPI_ORIGIN) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.FASTAPI_ORIGIN}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
