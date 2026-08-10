/** @type {import('next').NextConfig} */

// Rewrites are serialized into the build output at build time.
//   - API_URL: server-side destination for the /api/* rewrite. In Docker this
//     is the container-network URL (http://backend:8000); on Cloudflare it is
//     the public backend URL baked into the Worker.
//   - NEXT_PUBLIC_API_URL: inlined into the client bundle. In Docker this is
//     the browser-reachable URL (http://localhost:8000); on Cloudflare it is
//     the public backend URL used directly by the browser.
const REWRITE_TARGET = process.env.API_URL || "http://localhost:8000";

const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  webpack: (config) => {
    config.cache = false;
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${REWRITE_TARGET}/api/:path*`,
      },
    ];
  },
};

// Integrate Cloudflare bindings with the Next.js dev server only.
// @opennextjs/cloudflare is a devDependency; requiring it at runtime in the
// Docker standalone production image would fail.
if (process.env.NODE_ENV !== "production") {
  const { initOpenNextCloudflareForDev } = require("@opennextjs/cloudflare");
  initOpenNextCloudflareForDev();
}

module.exports = nextConfig;
