import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: [
        "localhost:3000",
        process.env.VERCEL_URL ?? "",
        process.env.CUSTOM_DOMAIN ?? "",
      ].filter(Boolean) as string[],
    },
  },
};

export default nextConfig;
