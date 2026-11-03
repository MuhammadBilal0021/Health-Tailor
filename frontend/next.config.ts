import type { NextConfig } from "next";
const config: NextConfig = {
  output: "standalone",
  experimental: { cpus: 2 },
  async rewrites() {
    // Same-origin API access for local development or separate-project hosting.
    const backend = process.env.BACKEND_URL;
    return backend
      ? [{ source: "/api/:path*", destination: `${backend}/api/:path*` }]
      : [];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};
export default config;
