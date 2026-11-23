import { expect, test } from "@playwright/test";

test.describe("Public entry", () => {
  test("the site opens directly on the sign-in page", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });

  test("no marketing landing or about page is served", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
  });
});
