import { expect, test, type Page } from "@playwright/test";

async function loginFaculty(page: Page, identifier: string, password: string) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Faculty", exact: true }).click();
  await page.locator("#identifier").fill(identifier);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: /Sign in as Faculty/i }).click();
  await expect(page).toHaveURL(/\/faculty/, { timeout: 20000 });
}

test.describe("Deep faculty insight and comment workflows (isolated test database)", () => {
  test("approved faculty reviews AI insights, question-wise performance and comparisons", async ({ page }) => {
    await loginFaculty(page, "alpha@test.local", "Test@12345");
    await page.goto("/faculty");
    await expect(page.getByText("Teaching overview").first()).toBeVisible({ timeout: 40000 });
    await expect(page.getByText("Question-wise performance").first()).toBeVisible({ timeout: 40000 });
    await expect(page.getByText("Academic-year comparison").first()).toBeVisible({ timeout: 40000 });
    await expect(page.getByText("AI insights").first()).toBeVisible({ timeout: 40000 });
    await expect(page.getByText("Strengths").first()).toBeVisible({ timeout: 40000 });
    await expect(page.getByText("Improvement areas and recommendations").first()).toBeVisible({ timeout: 40000 });
  });

  test("approved faculty views anonymous feedback comments", async ({ page }) => {
    await loginFaculty(page, "alpha@test.local", "Test@12345");
    await page.goto("/faculty/comments");
    await expect(page.getByText("Student comments").first()).toBeVisible({ timeout: 40000 });
    await expect(page.getByText(/Anonymous feedback/).first()).toBeVisible({ timeout: 40000 });
  });
});
