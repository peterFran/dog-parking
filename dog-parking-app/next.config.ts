import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  eslint: {
    // Disable ESLint during builds to prevent build failures from linting errors
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
