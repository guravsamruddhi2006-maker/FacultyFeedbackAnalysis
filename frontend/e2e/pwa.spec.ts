import { expect, test } from "@playwright/test";

test.describe("PWA and responsive shell", () => {
  test("exposes an installable manifest and touch icon", async ({ page, request }) => {
    await page.goto("/login");

    const manifestHref = await page.locator('link[rel="manifest"]').getAttribute("href");
    expect(manifestHref).toBe("/manifest.webmanifest");

    const manifest = await (await request.get("/manifest.webmanifest")).json();
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons.length).toBeGreaterThan(0);

    for (const icon of manifest.icons as Array<{ src: string }>) {
      const response = await request.get(icon.src);
      expect(response.ok()).toBe(true);
    }

    const touchIcon = page.locator('link[rel="apple-touch-icon"]');
    expect(await touchIcon.getAttribute("href")).toBe("/icons/apple-touch-icon.png");
  });

  test("serves a branded offline fallback", async ({ request }) => {
    const response = await request.get("/offline.html");
    expect(response.ok()).toBe(true);
    expect(await response.text()).toContain("You are offline");
  });

  for (const width of [320, 375, 430, 768, 1366, 1920]) {
    test(`sign-in page fits a ${width}px viewport without horizontal scrolling`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/login");

      await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);

      // Every interactive control must remain reachable at the narrowest width.
      await expect(page.getByLabel("USN")).toBeVisible();
      await expect(page.getByRole("button", { name: "Sign in as student" })).toBeVisible();
    });
  }
});
