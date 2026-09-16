import { test, expect } from "@playwright/test";

// Umbrella smoke (Issue #180): admin reaches every area with zero dead-ends.
// Heavy per-area proofs live in child issues (#174, #175, #176, #178, #179).
test("admin traverses all areas without dead-ends", async ({ page }) => {
  for (const route of [
    "/admin/dashboard",
    "/admin/users",
    "/admin/questions",
    "/admin/curriculum",
  ]) {
    await page.goto(route);
    await expect(page.getByText("Access Denied")).toHaveCount(0);
  }
});
