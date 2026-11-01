import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Site 100% estático: os dados vêm dos JSONs gerados pelo pipeline Python.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
