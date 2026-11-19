import { expect, test, type Page } from "@playwright/test";

test.describe("Deep student workflow: registration (isolated test database)", () => {
  test("student registration creates an account and returns to login", async ({ page }: { page: Page }) => {
    await page.goto("/register/student");
    await expect(page.getByRole("heading", { name: "Create a student account" })).toBeVisible();
    await page.locator("#name").fill("Deep E2E Test Student");
    await page.locator("#identifier").fill("4UB26CS003");
    await page.locator("#department_id").selectOption({ index: 1 });
    await page.locator("#password").fill("Test@12345");
    await page.locator("#confirm_password").fill("Test@12345");
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 30000 });
  });
});
