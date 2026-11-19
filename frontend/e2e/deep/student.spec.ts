import { expect, test, type Page } from "@playwright/test";

async function loginStudent(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: "Student", exact: true }).click();
  await page.locator("#identifier").fill("4UB26CS001");
  await page.locator("#password").fill("Test@12345");
  await page.getByRole("button", { name: /Sign in as Student/i }).click();
  await expect(page).toHaveURL(/\/student/, { timeout: 20000 });
}

test.describe("Deep student workflows (isolated test database)", () => {
  test("student login reaches dashboard", async ({ page }) => {
    await loginStudent(page);
    await expect(page.getByText(/Hello, Test/).first()).toBeVisible({ timeout: 30000 });
  });

  test("student submits feedback with ratings and comment", async ({ page }) => {
    await loginStudent(page);
    await page.getByRole("button", { name: /Give feedback/i }).first().click();
    await expect(page).toHaveURL(/\/student\/feedback\//, { timeout: 20000 });
    await expect(page.getByText("Rate each statement").first()).toBeVisible({ timeout: 30000 });

    const questionBlocks = page.locator("div.divide-y > div");
    await expect(questionBlocks).toHaveCount(5, { timeout: 30000 });
    for (let index = 0; index < 5; index += 1) {
      await questionBlocks.nth(index).locator("button").nth(4).click();
    }

    await page.locator("#comment").fill("Deep workflow E2E comment: teaching was engaging and examples were useful.");
    await page.getByRole("button", { name: "Submit anonymous feedback" }).click();
    await expect(page.getByText(/Feedback submitted/).first()).toBeVisible({ timeout: 30000 });
  });

  test("student edits feedback while period open", async ({ page }) => {
    await loginStudent(page);
    await page.goto("/student");
    await expect(page.getByRole("button", { name: "Edit", exact: true }).first()).toBeVisible({ timeout: 30000 });
    await page.getByRole("button", { name: "Edit", exact: true }).first().click();
    await expect(page).toHaveURL(/\/student\/feedback\//, { timeout: 20000 });
    await expect(page.getByText("Rate each statement").first()).toBeVisible({ timeout: 30000 });
    await expect(page.getByText("Editable").first()).toBeVisible({ timeout: 30000 });
    await expect(page.getByRole("button", { name: "Save changes" }).first()).toBeVisible({ timeout: 30000 });
    await page.locator("#comment").fill("Deep workflow E2E comment: updated teaching feedback text.");
    await page.getByRole("button", { name: "Save changes" }).click();
    await expect(page.getByText(/Feedback updated/).first()).toBeVisible({ timeout: 30000 });
  });
});
