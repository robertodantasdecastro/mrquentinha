import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "10.211.55.21",
    "10.211.55.2",
    "localhost",
    "127.0.0.1",
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
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
