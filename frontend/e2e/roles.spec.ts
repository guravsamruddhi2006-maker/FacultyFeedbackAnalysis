import { expect, test, type Page } from "@playwright/test";

const TAB_LABEL: Record<string, string> = {
  student: "Student",
  faculty: "Faculty",
  admin: "Administrator",
};

async function login(page: Page, role: "student" | "faculty" | "admin", identifier: string, password: string) {
  await page.goto("/login");
  await page.getByRole("button", { name: TAB_LABEL[role], exact: true }).click();
  await page.locator("#identifier").fill(identifier);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: new RegExp(`Sign in as ${TAB_LABEL[role]}`, "i") }).click();
}

test.describe("Authenticated role flows (local demo accounts)", () => {
  test("admin login reaches admin dashboard", async ({ page }) => {
    await login(page, "admin", "admin@test.local", "Test@12345");
    await expect(page).toHaveURL(/\/admin/, { timeout: 20000 });
    await expect(page.getByText("Department overview").first()).toBeVisible({ timeout: 30000 });
  });

  test("faculty login reaches faculty dashboard with insights", async ({ page }) => {
    await login(page, "faculty", "alpha@test.local", "Test@12345");
    await expect(page).toHaveURL(/\/faculty/, { timeout: 20000 });
    await expect(page.getByText("Teaching overview").first()).toBeVisible({ timeout: 30000 });
  });

  test("student login reaches student dashboard", async ({ page }) => {
    await login(page, "student", "4UB26CS001", "Test@12345");
    await expect(page).toHaveURL(/\/student/, { timeout: 20000 });
    await expect(page.getByText(/Hello,/).first()).toBeVisible({ timeout: 30000 });
  });
});
