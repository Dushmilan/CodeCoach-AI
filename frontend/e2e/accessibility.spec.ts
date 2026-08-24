import { test, expect } from "@playwright/test";
import { dismissOnboarding } from "./helpers/auth";

test.describe("Accessibility", () => {
  test("homepage has semantic header", async ({ page }) => {
    await page.goto("/");
    await dismissOnboarding(page);
    await expect(page.locator("header")).toBeVisible();
  });

  test("learn page has accessible navigation", async ({ page }) => {
    await page.goto("/learn");
    await expect(page.getByText("Learning Paths")).toBeVisible({ timeout: 15000 });
    const navLinks = page.locator("header").getByRole("link");
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test("page elements have descriptive text", async ({ page }) => {
    await page.goto("/");
    await dismissOnboarding(page);
    const bodyText = await page.textContent("body");
    expect(bodyText).toBeTruthy();
  });

  test("homepage primary CTA is reachable and activatable with the keyboard", async ({
    page,
  }) => {
    await page.goto("/");
    const cta = page.getByRole("link", { name: /start practicing →/i });
    await expect(cta).toBeVisible();
    await cta.focus();
    await expect(cta).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/problems/);
  });

  test("homepage advertises the step-by-step animation experience", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /see algorithms come alive/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /try it on a problem/i }),
    ).toBeVisible();
  });
});
