import { expect, test, type Page } from "@playwright/test";

async function loginAdmin(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Administrator", exact: true }).click();
  await page.locator("#identifier").fill("admin@test.local");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Administrator/i }).click();
  await expect(page).toHaveURL(/\/admin/, { timeout: 20000 });
}

async function loginFaculty(page: Page, identifier: string, password: string) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Faculty", exact: true }).click();
  await page.locator("#identifier").fill(identifier);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: /Sign in as Faculty/i }).click();
}

test.describe("Deep admin workflows (isolated test database)", () => {
  test("admin login reaches department overview with statistics", async ({ page }) => {
    await loginAdmin(page);
    await expect(page).toHaveURL(/\/admin/, { timeout: 20000 });
    await expect(page.getByText("Department overview").first()).toBeVisible({ timeout: 30000 });
  });

  test("admin faculty management lists registered faculty", async ({ page }) => {
    await loginAdmin(page);
    await page.goto("/admin/faculty");
    await expect(page.getByRole("heading", { name: "Faculty management" })).toBeVisible({ timeout: 40000 });
    await expect(page.getByText("Faculty Alpha").first()).toBeVisible({ timeout: 30000 });
    await expect(page.getByText("Faculty Pending").first()).toBeVisible({ timeout: 30000 });
  });

  test("pending faculty cannot log in before approval", async ({ page }) => {
    await loginFaculty(page, "pending@test.local", "Test@12345");
    await expect(page).toHaveURL(/\/login/, { timeout: 20000 });
    await expect(page.getByText(/awaiting administrator approval/i)).toBeVisible({ timeout: 20000 });
  });

  test("admin can approve a pending faculty account", async ({ page }) => {
    await loginAdmin(page);
    await page.goto("/admin/faculty");
    const pendingRow = page.locator("tr", { hasText: "Faculty Pending" });
    await expect(pendingRow).toBeVisible({ timeout: 40000 });
    await pendingRow.getByRole("button", { name: "Approve" }).click();
    await expect(pendingRow).toContainText("approved", { timeout: 40000 });
  });
});
