/** @type {import('next').NextConfig} */

// Rewrites are serialized into the build output at build time.
//   - API_URL: server-side destination for the /api/* rewrite. In Docker this
//     is the container-network URL (http://backend:8000); on Cloudflare it is
//     the public backend URL baked into the Worker.
//   - NEXT_PUBLIC_API_URL: inlined into the client bundle. In Docker this is
//     the browser-reachable URL (http://localhost:8000); on Cloudflare it is
//     the public backend URL used directly by the browser.
const REWRITE_TARGET = process.env.API_URL || 'http://localhost:8000';

const nextConfig = {
  env: {
    // Preserve an explicit empty value (same-origin, CSP-safe); only
    // fall back when the variable is unset. `||` would resurrect the
    // hardcoded URL for empty strings and get blocked by connect-src.
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
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
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Baseline hardening headers (mirrors the backend middleware).
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Permissions-Policy',
            value: 'geolocation=(), microphone=(), camera=()',
          },
          // CSP: keep Next.js + Monaco working ('unsafe-inline'/'unsafe-eval'
          // are required by hydration scripts and the editor) while blocking
          // the obvious XSS sinks (object-src, frame-ancestors, base-uri).
          // frame-src allows the Motion Canvas animation viewer (separate Vite
          // dev server on :9000 in E2E, or NEXT_PUBLIC_ANIMATION_VIEWER_URL in
          // prod) to load in an in-app iframe (see AnimateLauncher).
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: blob: https:",
              "font-src 'self' data:",
              "connect-src 'self' https: wss: ws:",
              "worker-src 'self' blob:",
              `frame-src 'self' ${process.env.NEXT_PUBLIC_ANIMATION_VIEWER_URL || 'http://localhost:9000'}`,
              "object-src 'none'",
              "base-uri 'self'",
              "frame-ancestors 'none'",
              "form-action 'self'",
            ].join('; '),
          },
        ],
      },
    ];
  },
};

// Integrate Cloudflare bindings with the Next.js dev server only.
// @opennextjs/cloudflare is a devDependency; requiring it at runtime in the
// Docker standalone production image would fail.
if (process.env.NODE_ENV !== 'production') {
  const { initOpenNextCloudflareForDev } = require('@opennextjs/cloudflare');
  initOpenNextCloudflareForDev();
}

module.exports = nextConfig;
