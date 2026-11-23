import { expect, test } from "@playwright/test";

const PROTECTED_PATHS = ["/student", "/faculty", "/admin"];

test.describe("Authentication guard (browser)", () => {
  for (const path of PROTECTED_PATHS) {
    test(`unauthenticated visit to ${path} redirects to login`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login/);
      await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    });
  }

  test("unauthenticated visit to home redirects to login", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });
});
