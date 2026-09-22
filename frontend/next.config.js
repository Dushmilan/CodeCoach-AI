/** @type {import('next').NextConfig} */

const { resolvePublicApiUrl } = require("./csp.js");

// Rewrites are serialized into the build output at build time.
//   - API_URL: server-side destination for the /api/* rewrite. In Docker this
//     is the container-network URL (http://backend:8000).
//   - NEXT_PUBLIC_API_URL: inlined into the client bundle. Defaults to
//     same-origin ('') so browser calls stay under CSP connect-src 'self'
//     and ride the /api rewrite; cross-origin deployments set an https:
//     origin explicitly. A hard-coded absolute http default would be
//     blocked by connect-src on every request (see #172).
const REWRITE_TARGET = process.env.API_URL || 'http://localhost:8000';

const nextConfig = {
  skipTrailingSlashRedirect: true,
  images: {
    // Taste 4.8 placeholder photography for the #230 landing surfaces.
    remotePatterns: [{ protocol: "https", hostname: "picsum.photos" }],
  },
  env: {
    NEXT_PUBLIC_API_URL: resolvePublicApiUrl(process.env),
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
          // script-src/style-src/font-src/connect-src/worker-src include cdn.jsdelivr.net
          // because @monaco-editor/react loads Monaco (loader.js + vs/*) from that CDN
          // via @monaco-editor/loader@1.7.0. Without this the editor stays at "Loading…".
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
              "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
              "img-src 'self' data: blob: https:",
              "font-src 'self' data: https://cdn.jsdelivr.net",
              "connect-src 'self' https: wss: ws: https://cdn.jsdelivr.net",
              "worker-src 'self' blob: https://cdn.jsdelivr.net",
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

module.exports = nextConfig;
