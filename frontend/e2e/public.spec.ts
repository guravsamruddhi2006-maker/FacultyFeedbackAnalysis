import { expect, test } from "@playwright/test";

test.describe("Public pages", () => {
  test("landing page renders headline and call to action", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/Turning student feedback into better teaching/i)).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(/Turning student feedback into better teaching/i);
  });

  test("about page renders mission content", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByText(/About FacultyInsight AI/i)).toBeVisible();
  });
});
