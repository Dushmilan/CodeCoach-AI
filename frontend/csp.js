/**
 * Resolves the browser-facing API base URL inlined into the client bundle.
 *
 * Default is same-origin (''): browser calls stay under CSP `connect-src
 * 'self'` and the Next.js /api rewrite proxies them to the backend.
 * Deployments with a genuinely cross-origin API set NEXT_PUBLIC_API_URL
 * explicitly (an https: origin, which connect-src already allows).
 *
 * An explicit empty value is preserved as-is; only an *unset* variable
 * falls back. (`||` would be equivalent here, but `??` documents that
 * empty-string means same-origin on purpose.)
 *
 * @param {NodeJS.ProcessEnv | Record<string, string | undefined>} env
 * @returns {string}
 */
function resolvePublicApiUrl(env) {
  return env.NEXT_PUBLIC_API_URL ?? "";
}

module.exports = { resolvePublicApiUrl };
