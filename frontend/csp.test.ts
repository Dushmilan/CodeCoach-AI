import { describe, expect, it } from "vitest";
import { resolvePublicApiUrl } from "./csp.js";

describe("resolvePublicApiUrl", () => {
  it("defaults to same-origin (empty) when unset", () => {
    // Regression: the old 'http://localhost:8000' fallback was posted to
    // directly by the browser and blocked by CSP connect-src on every login.
    // Same-origin keeps calls under 'self' via the /api rewrite.
    expect(resolvePublicApiUrl({})).toBe("");
  });

  it("preserves an explicit empty value (same-origin, CSP-safe)", () => {
    expect(resolvePublicApiUrl({ NEXT_PUBLIC_API_URL: "" })).toBe("");
  });

  it("preserves an explicit absolute URL for cross-origin deployments", () => {
    expect(
      resolvePublicApiUrl({
        NEXT_PUBLIC_API_URL: "https://api.example.com",
      }),
    ).toBe("https://api.example.com");
  });
});
