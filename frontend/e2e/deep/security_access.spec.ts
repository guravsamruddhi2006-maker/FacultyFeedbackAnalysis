import { expect, test, type Page } from "@playwright/test";

async function loginFaculty(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Faculty", exact: true }).click();
  await page.locator("#identifier").fill("alpha@test.local");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Faculty/i }).click();
  await expect(page).toHaveURL(/\/faculty/, { timeout: 20000 });
}

async function loginStudent(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Student", exact: true }).click();
  await page.locator("#identifier").fill("4UB26CS001");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Student/i }).click();
  await expect(page).toHaveURL(/\/student/, { timeout: 20000 });
}

async function loginAdmin(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Administrator", exact: true }).click();
  await page.locator("#identifier").fill("admin@test.local");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Administrator/i }).click();
  await expect(page).toHaveURL(/\/admin/, { timeout: 20000 });
}

test.describe("Deep security: cross-role page access (isolated test database)", () => {
  test("faculty cannot open admin pages", async ({ page }) => {
    await loginFaculty(page);
    await page.goto("/admin");
    await expect(page.getByText("Access denied").first()).toBeVisible({ timeout: 40000 });
  });

  test("student cannot open admin pages", async ({ page }) => {
    await loginStudent(page);
    await page.goto("/admin");
    await expect(page.getByText("Access denied").first()).toBeVisible({ timeout: 40000 });
  });

  test("admin cannot open student pages", async ({ page }) => {
    await loginAdmin(page);
    await page.goto("/student");
    await expect(page.getByText("Access denied").first()).toBeVisible({ timeout: 40000 });
  });
});
