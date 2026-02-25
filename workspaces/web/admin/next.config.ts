import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "http://10.211.55.21:3002",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
  ],
  transpilePackages: ["@mrquentinha/ui"],
  experimental: { externalDir: true },
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "10.211.55.21",
        port: "8000",
        pathname: "/media/**",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "8000",
        pathname: "/media/**",
      },
      {
        protocol: "https",
        hostname: "api.mrquentinha.com.br",
        pathname: "/media/**",
      },
    ],
  },
};

export default nextConfig;
