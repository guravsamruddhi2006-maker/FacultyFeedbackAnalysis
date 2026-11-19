import { expect, test, type Page } from "@playwright/test";

async function loginAdmin(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Administrator", exact: true }).click();
  await page.locator("#identifier").fill("admin@test.local");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Administrator/i }).click();
  await expect(page).toHaveURL(/\/admin/, { timeout: 20000 });
}

test.describe("Deep admin catalog, period and audit workflows (isolated test database)", () => {
  test("admin opens catalog management and reviews feedback period schedule", async ({ page }) => {
    await loginAdmin(page);
    await page.goto("/admin/catalog");
    await expect(page.getByRole("heading", { name: "Catalog management" })).toBeVisible({ timeout: 40000 });
    await page.getByRole("button", { name: "Feedback periods" }).click();
    const periodRow = page.locator("tr", { hasText: "2026-27" });
    await expect(periodRow).toBeVisible();
    await expect(periodRow).toContainText("Open");
  });

  test("admin opens audit log page", async ({ page }) => {
    await loginAdmin(page);
    await page.goto("/admin/audit");
    await expect(page.getByRole("heading", { name: "Audit log" })).toBeVisible({ timeout: 40000 });
    await expect(page.getByText(/Recent events/).first()).toBeVisible();
  });

  test("admin registers a pending faculty and rejects them", async ({ page }) => {
    await page.goto("/register/faculty");
    await expect(page.getByRole("heading", { name: "Faculty registration" })).toBeVisible();
    await page.locator("#name").fill("Deep E2E Faculty");
    await page.locator("#identifier").fill("deep-e2e-faculty@test.local");
    await page.locator("#department_id").selectOption({ index: 1 });
    await page.locator("#password").fill("Test@12345");
    await page.locator("#confirm_password").fill("Test@12345");
    await page.getByRole("button", { name: "Submit registration" }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 30000 });

    await loginAdmin(page);
    await page.goto("/admin/faculty");
    const newFacultyRow = page.locator("tr", { hasText: "Deep E2E Faculty" });
    await expect(newFacultyRow).toBeVisible({ timeout: 40000 });
    await newFacultyRow.getByRole("button", { name: "Reject" }).click();
    await expect(newFacultyRow).toContainText("rejected", { timeout: 40000 });
  });
});
