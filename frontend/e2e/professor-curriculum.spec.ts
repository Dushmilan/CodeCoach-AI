import { test, expect } from "@playwright/test";

test("professor curriculum has no /admin links", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("domcontentloaded");
  await page.getByLabel(/username/i).fill("professor.ada");
  await page.getByLabel(/password/i).fill("professor123");
  await page.getByRole("main").getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL("/professor", { timeout: 15000 });
  await page.goto("/professor/curriculum");
  await expect(page.getByRole("heading", { name: /curriculum/i })).toBeVisible();
  const adminLinks = await page.locator('a[href^="/admin"]').count();
  expect(adminLinks).toBe(0);
});
