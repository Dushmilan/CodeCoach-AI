import { test, expect } from "@playwright/test";

test("professor curriculum has no /admin links", async ({ page }) => {
  await page.goto("/professor/curriculum");
  await expect(page.getByRole("heading", { name: /curriculum/i })).toBeVisible();
  const adminLinks = await page.locator('a[href^="/admin"]').count();
  expect(adminLinks).toBe(0);
});
