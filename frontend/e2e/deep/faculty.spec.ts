import { expect, test, type Page } from "@playwright/test";

test("approved faculty reaches teaching dashboard with insights", async ({ page }: { page: Page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Faculty", exact: true }).click();
  await page.locator("#identifier").fill("alpha@test.local");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Faculty/i }).click();
  await expect(page).toHaveURL(/\/faculty/, { timeout: 20000 });
  await expect(page.getByText("Teaching overview").first()).toBeVisible({ timeout: 30000 });
});
